from typing import Dict, Optional, Any
from logging import getLogger
from contextlib import closing

from librabbitmq import Connection

import missive
from missive.shutdown_handler import ShutdownHandler


logger = getLogger(__name__)


class RabbitMQAdapter(missive.Adapter[missive.M]):
    def __init__(self, message_cls, processor) -> None:
        self.message_cls = message_cls
        self.processor = processor
        self._delivery_tags: Dict[bytes, int] = {}
        self.shutdown_handler = ShutdownHandler()

    def ack(self, message: missive.M) -> None:
        delivery_tag = self._delivery_tags.pop(message.message_id)
        self.channel.basic_ack(delivery_tag)
        logger.info("acked (%d) %s", delivery_tag, message)

    def nack(self, message: missive.M) -> None:
        raise NotImplementedError("not implemented!")

    def run(self) -> None:
        with closing(Connection()) as conn:
            with self.processor.handling_context(self.message_cls, self) as ctx:
                with closing(conn.channel()) as channel:
                    self.channel = channel

                    def callback(rabbit_message):
                        logger.debug("got message from rabbitmq: %s", rabbit_message)
                        message = self.message_cls(bytes(rabbit_message.body))
                        self._delivery_tags[message.message_id] = rabbit_message.delivery_info["delivery_tag"]
                        ctx.handle(message)

                    channel.basic_consume("test", callback=callback)

                    while not self.shutdown_handler.should_exit():
                        conn.drain_events()
                logger.info("closed channel")
        logger.info("closed connection")

from typing import Dict, Any, Type
from logging import getLogger
from contextlib import ExitStack

from librabbitmq import Connection

import missive
from missive.shutdown_handler import ShutdownHandler


logger = getLogger(__name__)


class RabbitMQAdapter(missive.Adapter[missive.M]):
    def __init__(
        self,
        message_cls: Type[missive.M],
        processor: missive.Processor[missive.M],
        queue: str,
    ) -> None:
        self.message_cls = message_cls
        self.processor = processor
        self._delivery_tags: Dict[bytes, int] = {}
        self.shutdown_handler = ShutdownHandler()
        self.channel: Any = None
        self.queue = queue

    def ack(self, message: missive.M) -> None:
        delivery_tag = self._delivery_tags.pop(message.message_id)
        self.channel.basic_ack(delivery_tag)
        logger.info("acked (%d) %s", delivery_tag, message)

    def nack(self, message: missive.M) -> None:
        raise NotImplementedError("not implemented!")

    def run(self) -> None:
        with ExitStack() as stack:
            conn = stack.enter_context(Connection())
            channel = stack.enter_context(conn.channel())
            ctx = stack.enter_context(
                self.processor.handling_context(self.message_cls, self)
            )

            logger.info("channel opened: %s, (%s)", channel.channel_id, conn)
            self.channel = channel

            def callback(rabbit_message: Any) -> None:
                message = self.message_cls(bytes(rabbit_message.body))
                delivery_tag: int = rabbit_message.delivery_info["delivery_tag"]
                logger.debug(
                    "got message from rabbitmq: %s (%d)", rabbit_message, delivery_tag,
                )
                self._delivery_tags[message.message_id] = delivery_tag
                ctx.handle(message)

            channel.basic_consume(self.queue, callback=callback)
            logger.info("consuming from %s", self.queue)

            while not self.shutdown_handler.should_exit():
                conn.drain_events()
        logger.info("closed connection and channel")

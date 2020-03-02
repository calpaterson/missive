from typing import Dict, Optional, Any
from logging import getLogger
from contextlib import closing

import pika

import missive


logger = getLogger(__name__)


class RabbitMQAdapter(missive.Adapter[missive.M]):
    def __init__(self, message_cls, processor) -> None:
        self.message_cls = message_cls
        self.processor = processor
        self._delivery_tags: Dict[bytes, int] = {}
        self.channel: Optional[Any] = None

    def ack(self, message: missive.M) -> None:
        delivery_tag = self._delivery_tags.pop(message.message_id)
        self.channel.basic_ack(delivery_tag)
        logger.info("acked (%d) %s", delivery_tag, message)

    def nack(self, message: missive.M) -> None:
        raise NotImplementedError("not implemented!")

    def run(self) -> None:
        with closing(pika.BlockingConnection()) as conn:
            with self.processor.handling_context(self.message_cls, self) as ctx:
                self.channel = conn.channel()
                for method_frame, properties, body in self.channel.consume("test"):
                    logger.info(
                        "got message: %s, %s, %s", method_frame, properties, body
                    )
                    message = self.message_cls(body)
                    self._delivery_tags[message.message_id] = method_frame.delivery_tag
                    ctx.handle(self.message_cls(body))

from typing import Any, Type
from logging import getLogger
from contextlib import ExitStack
import socket

import kombu

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
        self.shutdown_handler = ShutdownHandler()
        self.queue = queue

    def ack(self, message: missive.M) -> None:
        self._current_kombu_message.ack()
        logger.info("acked %s", message)

    def nack(self, message: missive.M) -> None:
        raise NotImplementedError("not implemented!")

    def run(self) -> None:
        self.shutdown_handler.enable()
        with ExitStack() as stack:
            conn = stack.enter_context(kombu.Connection())
            queue = kombu.Queue(self.queue)
            consumer = stack.enter_context(kombu.Consumer(conn, [queue]))

            ctx = stack.enter_context(
                self.processor.handling_context(self.message_cls, self)
            )

            def callback(kombu_message: Any) -> None:
                message = self.message_cls(bytes(kombu_message.body))
                self._current_kombu_message = kombu_message
                logger.info(
                    "got message from rabbitmq: %s ", kombu_message,
                )
                ctx.handle(message)

            consumer.on_message = callback

            logger.info("consuming from %s", queue)

            while not self.shutdown_handler.should_exit():
                try:
                    conn.drain_events(timeout=5)
                except socket.timeout:
                    # when the timeout is hit this exception is raised
                    pass
        logger.info("closed connection")

from typing import Any, Type, Sequence
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
        queues: Sequence[str],
        url_or_conn: Any = "amqp://",
        disable_shutdown_handler: bool = False,
        drain_timeout: int = 1,
    ) -> None:
        self.message_cls = message_cls
        self.processor = processor
        self.shutdown_handler = ShutdownHandler()
        self.url_or_conn = url_or_conn
        self.queues = queues
        self.disable_shutdown_handler = disable_shutdown_handler
        self.drain_timeout = drain_timeout

    def ack(self, message: missive.M) -> None:
        self._current_kombu_message.ack()
        logger.debug("acked %s", message)

    def nack(self, message: missive.M) -> None:
        raise NotImplementedError("not implemented!")

    def _get_conn(self, url_or_conn: Any, stack: ExitStack) -> Any:
        """Either we were passed a url or a real conn - either way get us a
        working conn."""
        if isinstance(url_or_conn, kombu.Connection):
            return url_or_conn
        else:
            # If we're creating the conn, put it on the stack so it gets closed
            # when we exit
            return stack.enter_context(kombu.Connection(self.url_or_conn))

    def run(self) -> None:
        if not self.disable_shutdown_handler:
            self.shutdown_handler.enable()

        with ExitStack() as stack:
            conn = self._get_conn(self.url_or_conn, stack)
            channel = stack.enter_context(conn.channel())
            logger.info("connected to %s", conn.as_uri())

            queues = [kombu.Queue(queue, channel=channel) for queue in self.queues]
            consumer = kombu.Consumer(channel, queues)

            ctx = stack.enter_context(
                self.processor.handling_context(self.message_cls, self)
            )

            def callback(body: Any, kombu_message: Any) -> None:
                message = self.message_cls(bytes(kombu_message.body))
                self._current_kombu_message = kombu_message
                logger.debug(
                    "got message from rabbitmq: %s ", kombu_message,
                )
                ctx.handle(message)

            consumer.register_callback(callback)

            # Enter the consumer's context ONLY after registering callbacks
            stack.enter_context(consumer)

            logger.debug("consuming from %s", queues)

            drain_timeout = self.drain_timeout
            while not self.shutdown_handler.should_exit():
                try:
                    conn.drain_events(timeout=drain_timeout)
                except socket.timeout:
                    # when the timeout is hit this exception is raised
                    pass
        logger.info("closed connection")

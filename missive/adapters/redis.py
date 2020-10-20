import time
import threading
from logging import getLogger
from typing import Type, Sequence, Optional, Dict, Any

import missive
from missive.shutdown_handler import ShutdownHandler

import redis

logger = getLogger(__name__)


class RedisPubSubAdapter(missive.Adapter[missive.M]):
    def __init__(
        self,
        message_cls: Type[missive.M],
        processor: missive.Processor[missive.M],
        channels: Sequence[str],
    ) -> None:
        self.processor = processor
        self.message_cls = message_cls
        self.redis = redis.Redis()
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self.shutdown_handler = ShutdownHandler()
        self.channels = channels
        self.thread: Optional[threading.Thread] = None
        self.thread_sleep = 0.001

    def ack(self, message: missive.M) -> None:
        pass

    def nack(self, message: missive.M) -> None:
        pass

    def run(self) -> None:
        with self.processor.context(self.message_cls, self) as ctx:

            def handler(message: Dict[Any, Any]) -> None:
                logger.debug("got redis message: %s", message)
                ctx.handle(self.message_cls(message["data"]))

            self.pubsub.subscribe(**{channel: handler for channel in self.channels})
            logger.info("subscribed to channels: %s", self.channels)

            self.thread = self.pubsub.run_in_thread(sleep_time=self.thread_sleep)  # type: ignore
            logger.info("started thread: %s", self.thread)

            self.shutdown_handler.wait_for_flag()
            self.thread.stop()  # type: ignore
            logger.info("shutting down")

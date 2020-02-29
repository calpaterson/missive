import time
import threading
from logging import getLogger
from typing import Type, Sequence, Optional, Dict, Any

import missive

import redis

logger = getLogger(__name__)


class ShutdownHandler:
    def __init__(self) -> None:
        self.flag = False

    def should_exit(self) -> bool:
        return self.flag

    def set_flag(self) -> None:
        logger.warning("setting flag!")
        self.flag = True


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

    def ack(self, message: missive.M) -> None:
        pass

    def nack(self, message: missive.M) -> None:
        pass

    def run(self) -> None:
        with self.processor.handling_context(self.message_cls, self) as ctx:

            def handler(message: Dict[Any, Any]) -> None:
                logger.debug("got redis message: %s", message)
                ctx.handle(self.message_cls(message["data"]))

            self.pubsub.subscribe(**{channel: handler for channel in self.channels})
            logger.info("subscribed to channels: %s", self.channels)

            self.thread = self.pubsub.run_in_thread(sleep_time=0.001)  # type: ignore
            logger.info("started thread: %s", self.thread)

            while not self.shutdown_handler.should_exit():
                time.sleep(0.1)
            self.thread.stop()  # type: ignore
            logger.info("shutting down")

from typing import Any, Callable, Optional
import threading
from logging import getLogger
import signal

logger = getLogger(__name__)


class ShutdownHandler:
    def __init__(self, callback: Optional[Callable[[int], None]] = None) -> None:
        self.flag = threading.Event()
        self.callback = callback

    def enable(self) -> None:
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def should_exit(self) -> bool:
        return self.flag.is_set()

    def signal_handler(self, signal: int, frame: Any) -> None:
        logger.info("got signal %d, %s", signal, frame)
        if self.callback is not None:
            self.callback(signal)
        self.set_flag()

    def set_flag(self) -> None:
        logger.warning("setting shutdown flag!")
        self.flag.set()

    def wait_for_flag(self) -> None:
        self.flag.wait()
        logger.info("stopped waiting for flag")

import threading
from logging import getLogger

logger = getLogger(__name__)


class ShutdownHandler:
    def __init__(self) -> None:
        self.flag = threading.Event()

    def should_exit(self) -> bool:
        return self.flag.is_set()

    def set_flag(self) -> None:
        logger.warning("setting flag!")
        self.flag.set()

    def wait_for_flag(self) -> None:
        self.flag.wait()
        logger.info("stopped waiting for flag")

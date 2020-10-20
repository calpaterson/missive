import os
from select import select
import sys
from typing import Type, BinaryIO, Optional
from logging import getLogger
from io import BytesIO

from missive import Adapter, Processor, M
from missive.shutdown_handler import ShutdownHandler

logger = getLogger(__name__)

_CHUNK_SIZE = 4096


class StdinAdapter(Adapter[M]):
    def __init__(
        self,
        message_cls: Type[M],
        processor: Processor[M],
        filelike: Optional[BinaryIO] = None,
    ) -> None:
        self.processor = processor
        self.message_cls = message_cls
        if filelike is None:
            self.filelike = sys.stdin.buffer
        else:
            self.filelike = filelike
        self.shutdown_handler = ShutdownHandler()

    def ack(self, message: M) -> None:
        pass

    def nack(self, message: M) -> None:
        raise NotImplementedError("No nack for stdin")

    def run(self) -> None:
        logger.info("started")
        with self.processor.context(self.message_cls, self) as ctx:
            while not self.shutdown_handler.should_exit():
                # FIXME: rewrite this to use selectors instead of low level select
                select([self.filelike], [], [])
                content: bytes = os.read(self.filelike.fileno(), _CHUNK_SIZE)
                for line in content.splitlines():
                    logger.info("got line")
                    logger.info(line)
                    data = line.rstrip()
                    ctx.handle(self.message_cls(raw_data=data))

import sys
from typing import Type

from ..missive import Adapter, Processor, GenericMessage, M


class StdinAdapter(Adapter[M]):
    def __init__(self, message_cls: Type[M], processor: Processor[M]) -> None:
        self.processor = processor
        self.message_cls = message_cls

    def run(self) -> None:
        with self.processor.handling_context(self.message_cls, self) as ctx:
            for line in sys.stdin:
                data = line.rstrip().encode("utf-8")
                ctx.handle(self.message_cls(raw_data=data))

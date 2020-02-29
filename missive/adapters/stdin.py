import sys

from ..missive import Adapter, Processor, GenericMessage


class StdinAdapter(Adapter[GenericMessage]):
    def __init__(self, processor: Processor[GenericMessage]) -> None:
        self.processor = processor

    def run(self) -> None:
        with self.processor.handling_context(self) as ctx:
            for line in sys.stdin:
                data = line.rstrip().encode("utf-8")
                ctx.handle(GenericMessage(raw_data=data))

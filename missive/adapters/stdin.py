import sys

from ..missive import Adapter, Processor
from ..messages import GenericMessage


class StdinAdapter(Adapter[GenericMessage]):
    def __init__(self, processor: Processor[GenericMessage]) -> None:
        self.processor = processor

    def run(self) -> None:
        for line in sys.stdin:
            data = line.rstrip().encode("utf-8")
            self.processor.handle(GenericMessage(data))

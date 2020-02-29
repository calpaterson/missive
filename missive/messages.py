from typing import Callable, Dict, Optional, Any

from .missive import Message, logger


class DictMessage(Message):
    def __init__(self, raw_data: bytes, decoder: Callable[[bytes], Dict[Any, Any]]):
        self.decoder = decoder
        self._decoded: Optional[Dict[Any, Any]] = None
        super().__init__(raw_data=raw_data)

    def contents(self) -> Dict[Any, Any]:
        if self._decoded is None:
            self._decoded = self.decoder(self.raw_data)
        return self._decoded

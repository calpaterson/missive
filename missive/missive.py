import abc
from dataclasses import dataclass
from logging import getLogger
from typing import Callable, MutableMapping, Tuple

logger = getLogger("missive")


class Message(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def ack(self):
        ...

    @abc.abstractmethod
    def nack(self):
        ...


class TestMessage(Message):
    def __init__(self):
        super()
        self.acked = False
        self.nacked = False

    def ack(self):
        self.acked = True

    def nack(self):
        self.nacked = True


class Adapter:
    ...


class StdinAdapter(Adapter):
    ...


class TestClient:
    def __init__(self, processor: "Processor"):
        self.processor = processor

    def send(self, message: TestMessage) -> None:
        self.processor.handle(message)


Matcher = Callable[[Message], bool]

Handler = Callable[[Message], None]


class Processor:
    def __init__(self):
        self.handlers: MutableMapping[Tuple[Matcher], Handler] = {}

    def handle_for(self, matchers: Tuple[Matcher]) -> Callable:
        def wrapper(fn) -> None:
            self.handlers[matchers] = fn

        return wrapper

    def handle(self, message: Message) -> None:
        handled = False
        for matchers, handler in self.handlers.items():
            if all(matcher(message) for matcher in matchers):
                handler(message)
                handled = True

        if not handled:
            logger.critical(
                "no matching handlers and no dlq configured, crashing on %s", message
            )
            raise RuntimeError("no matching handler")

    def test_client(self) -> TestClient:
        return TestClient(self)

    def run(self, adapter: Adapter):
        ...

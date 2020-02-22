import abc
import sys
from logging import getLogger
from typing import Callable, MutableMapping, Tuple

logger = getLogger("missive")


class Message(metaclass=abc.ABCMeta):
    def __init__(self, data: bytes = b"") -> None:
        self.data = data

    @abc.abstractmethod
    def ack(self) -> None:
        ...

    @abc.abstractmethod
    def nack(self) -> None:
        ...

    def __repr__(self) -> str:
        return "<%s (%r)>" % (self.__class__.__name__, self.data)

    def __str__(self) -> str:
        return repr(self)


class GenericMessage(Message):
    def ack(self) -> None:
        logger.info("acked: %s", self)

    def nack(self) -> None:
        logger.info("nacked: %s", self)


class TestMessage(Message):
    def __init__(self) -> None:
        super()
        self.acked = False
        self.nacked = False

    def ack(self) -> None:
        self.acked = True

    def nack(self) -> None:
        self.nacked = True


class Adapter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, processor: "Processor"):
        ...


class StdinAdapter(Adapter):
    def __init__(self, processor: "Processor"):
        self.processor = processor

    def run(self) -> None:
        for line in sys.stdin:
            data = line.rstrip().encode("utf-8")
            self.processor.handle(GenericMessage(data))


class TestClient:
    def __init__(self, processor: "Processor"):
        self.processor = processor

    def send(self, message: TestMessage) -> None:
        self.processor.handle(message)


Matcher = Callable[[Message], bool]

Handler = Callable[[Message], None]


class Processor:
    def __init__(self) -> None:
        self.handlers: MutableMapping[Tuple[Matcher], Handler] = {}

    def handle_for(self, matchers: Tuple[Matcher]) -> Callable[[Handler], None]:
        def wrapper(fn: Handler) -> None:
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

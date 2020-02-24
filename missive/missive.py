import abc
import uuid
from logging import getLogger
import collections.abc
from datetime import datetime
from typing import Callable, MutableMapping, Sequence, FrozenSet, Optional, Tuple

logger = getLogger("missive")


class Message(metaclass=abc.ABCMeta):
    def __init__(self, data: bytes = b"") -> None:
        self.data = data
        self.message_id = uuid.uuid4().bytes

    @abc.abstractmethod
    def ack(self) -> None:
        ...

    @abc.abstractmethod
    def nack(self) -> None:
        ...

    def __repr__(self) -> str:
        return "<%s (%r, %r)>" % (
            self.__class__.__name__,
            self.message_id.hex(),
            self.data[:30],
        )

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        else:
            return self.message_id == other.message_id


class TestMessage(Message):
    def __init__(self) -> None:
        super().__init__()
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


class TestClient:
    def __init__(self, processor: "Processor"):
        self.processor = processor

    def send(self, message: TestMessage) -> None:
        self.processor.handle(message)


DLQ = MutableMapping[bytes, Tuple[Message, str]]

Matcher = Callable[[Message], bool]

Handler = Callable[[Message], None]


class Processor:
    def __init__(self) -> None:
        self.handlers: MutableMapping[FrozenSet[Matcher], Handler] = {}
        self.dlq: Optional[DLQ] = None

    def handle_for(self, matchers: Sequence[Matcher]) -> Callable[[Handler], None]:
        def wrapper(fn: Handler) -> None:
            self.handlers[frozenset(matchers)] = fn

        return wrapper

    def set_dlq(self, dlq: DLQ) -> None:
        self.dlq = dlq

    def handle(self, message: Message) -> None:
        matching_handlers = []
        for matchers, handler in self.handlers.items():
            if all(matcher(message) for matcher in matchers):
                logger.debug("matched %s for %s", handler, message)
                matching_handlers.append(handler)
            else:
                logger.debug("did not match %s for %s", handler, message)

        if len(matching_handlers) == 0:
            reason = "no matching handlers"
            if self.dlq is not None:
                logger.warning("no matching handlers for %s - putting on dlq", message)
                self.dlq[message.message_id] = (message, reason)
                message.ack()
                return
            else:
                logger.critical(
                    "no matching handlers and no dlq configured, crashing on %s",
                    message,
                )
                raise RuntimeError("no matching handler")

        if len(matching_handlers) > 1:
            reason = "multiple matching handlers"
            if self.dlq is not None:
                logger.warning(
                    "multiple matching handlers for %s - putting on dlq", message
                )
                self.dlq[message.message_id] = (message, reason)
                message.ack()
                return
            logger.critical(
                "multiple matching handlers and no dlq configured, crashing on %s",
                message,
            )
            raise RuntimeError("multiple matching handlers")

        sole_matching_handler = matching_handlers[0]
        logger.debug("calling %s", sole_matching_handler)
        sole_matching_handler(message)

    def test_client(self) -> TestClient:
        return TestClient(self)

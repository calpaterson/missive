import abc
import json
import uuid
from contextlib import contextmanager
from logging import getLogger
from typing import (
    ContextManager,
    Callable,
    MutableMapping,
    Sequence,
    FrozenSet,
    Optional,
    Tuple,
    Generic,
    TypeVar,
    Union,
    List,
    Dict,
    Any,
    Iterator,
    Type,
)

logger = getLogger("missive")


class Message(metaclass=abc.ABCMeta):
    def __init__(self, raw_data: bytes) -> None:
        self.raw_data = raw_data
        self.message_id = uuid.uuid4().bytes

    def __repr__(self) -> str:
        return "<%s (%r, %r)>" % (
            self.__class__.__name__,
            self.message_id.hex(),
            self.raw_data[:30],
        )

    def __str__(self) -> str:
        return repr(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return False
        else:
            return self.message_id == other.message_id


class GenericMessage(Message):
    ...


class JSONMessage(Message):
    def __init__(self, raw_data: bytes) -> None:
        super().__init__(raw_data)
        self._json: Optional[Any] = None

    def get_json(self) -> Any:
        if self._json is None:
            self._json = json.loads(self.raw_data.decode("utf-8"))
            return self._json
        else:
            return self._json


M = TypeVar("M", bound=Message)


class Adapter(Generic[M], metaclass=abc.ABCMeta):
    """Abstract base class representing the API between :class:`missive.Processor` and adapters.

    """

    @abc.abstractmethod
    def __init__(self, processor: "Processor[M]"):
        ...

    @abc.abstractmethod
    def ack(self, message: M) -> None:
        """Mark a message as acknowledged.

        :param message: The message object to be acknowledged.

        """

    @abc.abstractmethod
    def nack(self, message: M) -> None:
        """Mark a message as negatively acknowledged.

        The meaning of this can vary depending on the message transport in
        question but generally it either returns the message to the message bus
        queue from which it came or triggers some special processing via some
        (message bus specific) dead letter queue.

        :param message: The message object to be acknowledged.

        """
        ...


class TestAdapter(Adapter[M]):
    def __init__(self, processor: "Processor[M]"):
        self.processor = processor
        self.acked: List[M] = []
        self.nacked: List[M] = []

    def ack(self, message: M) -> None:
        self.acked.append(message)

    def nack(self, message: M) -> None:
        self.nacked.append(message)

    def send(self, message: M) -> None:
        ctx: "HandlingContext[M]"
        with self.processor.handling_context(type(message), self) as ctx:
            ctx.handle(message)


DLQ = MutableMapping[bytes, Tuple[M, str]]

Matcher = Callable[[M], bool]

Handler = Callable[[M, "HandlingContext[M]"], None]


class HandlingContext(Generic[M]):
    def __init__(
        self, message_cls: Type[M], adapter: Adapter[M], processor: "Processor[M]"
    ) -> None:
        self.message_cls = message_cls
        self.adapter = adapter
        self.processor = processor

    def ack(self, message: M) -> None:
        self.adapter.ack(message)

    def nack(self, message: M) -> None:
        self.adapter.nack(message)

    def handle(self, message: M) -> None:
        matching_handlers = []
        for matchers, handler in self.processor.handlers.items():
            if all(matcher(message) for matcher in matchers):
                logger.debug("matched %s for %s", handler, message)
                matching_handlers.append(handler)
            else:
                logger.debug("did not match %s for %s", handler, message)

        if len(matching_handlers) == 0:
            reason = "no matching handlers"
            if self.processor.dlq is not None:
                logger.warning("no matching handlers for %s - putting on dlq", message)
                self.processor.dlq[message.message_id] = (message, reason)
                self.ack(message)
                return
            else:
                logger.critical(
                    "no matching handlers and no dlq configured, crashing on %s",
                    message,
                )
                raise RuntimeError("no matching handler")

        if len(matching_handlers) > 1:
            reason = "multiple matching handlers"
            if self.processor.dlq is not None:
                logger.warning(
                    "multiple matching handlers for %s - putting on dlq", message
                )
                self.processor.dlq[message.message_id] = (message, reason)
                self.ack(message)
                return
            logger.critical(
                "multiple matching handlers and no dlq configured, crashing on %s",
                message,
            )
            raise RuntimeError("multiple matching handlers")

        sole_matching_handler = matching_handlers[0]
        logger.debug("calling %s", sole_matching_handler)
        sole_matching_handler(message, self)


class Processor(Generic[M]):
    def __init__(self) -> None:
        self.handlers: MutableMapping[FrozenSet[Matcher[M]], Handler[M]] = {}
        self.dlq: Optional[DLQ[M]] = None

    def handle_for(
        self, matchers: Sequence[Matcher[M]]
    ) -> Callable[[Handler[M]], None]:
        def wrapper(fn: Handler[M]) -> None:
            self.handlers[frozenset(matchers)] = fn

        return wrapper

    def set_dlq(self, dlq: DLQ[M]) -> None:
        self.dlq = dlq

    @contextmanager
    def handling_context(
        self, message_cls: Type[M], adapter: Adapter[M]
    ) -> Iterator[HandlingContext[M]]:
        yield HandlingContext(message_cls, adapter, self)

    def test_client(self) -> TestAdapter[M]:
        return TestAdapter(self)

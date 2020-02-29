import abc
import json
import uuid
from logging import getLogger
from typing import (
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
)

logger = getLogger("missive")


class Message(metaclass=abc.ABCMeta):
    def __init__(self, raw_data: bytes = b"") -> None:
        self.raw_data = raw_data
        self.message_id = uuid.uuid4().bytes

    # FIXME: refer to adapter here
    # @abc.abstractmethod
    def ack(self) -> None:
        ...

    # @abc.abstractmethod
    def nack(self) -> None:
        ...

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


class TestMessage(Message):
    def __init__(self) -> None:
        super().__init__()
        self.acked = False
        self.nacked = False

    def ack(self) -> None:
        self.acked = True

    def nack(self) -> None:
        self.nacked = True


class JSONMessage(Message):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._json: Optional[Union[List[Dict[Any, Any]], Dict[Any, Any]]] = None

    def get_json(self) -> Union[List[Dict[Any, Any]], Dict[Any, Any]]:
        if self._json is None:
            self._json = json.loads(self.raw_data.decode("utf-8"))
            return self._json
        else:
            return self._json


M = TypeVar("M", bound=Message)


class Adapter(Generic[M], metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def __init__(self, processor: "Processor[M]"):
        ...


class TestClient(Generic[M]):
    def __init__(self, processor: "Processor[M]"):
        self.processor = processor

    def send(self, message: M) -> None:
        self.processor.handle(message)


DLQ = MutableMapping[bytes, Tuple[M, str]]

Matcher = Callable[[M], bool]

Handler = Callable[[M], None]


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

    def handle(self, message: M) -> None:
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

    def test_client(self) -> TestClient[M]:
        return TestClient(self)

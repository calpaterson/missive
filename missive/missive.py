import abc
import json
import uuid
from dataclasses import dataclass
from contextlib import contextmanager, ExitStack, closing
from logging import getLogger
from typing import (
    MutableSequence,
    Callable,
    MutableMapping,
    Optional,
    Tuple,
    Generic,
    TypeVar,
    List,
    Any,
    Iterator,
    Type,
    Set,
)

logger = getLogger("missive")

from .state import State


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


class RawMessage(Message):
    """A raw message of just bytes with no interpretation"""

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


class TestAdapter(Adapter[M]):
    # Tell pytest not to try and collect this class
    __test__ = False

    def __init__(self, processor: "Processor[M]"):
        self.processor = processor
        self.acked: List[M] = []
        self.nacked: List[M] = []
        self.stack = ExitStack()
        self.ctx: Optional[ProcessingContext[M]] = None

    def ack(self, message: M) -> None:
        self.acked.append(message)

    def nack(self, message: M) -> None:
        self.nacked.append(message)

    def send(self, message: M) -> None:
        if self.ctx is None:
            self.ctx = self.stack.enter_context(
                self.processor.context(type(message), self)
            )
        self.ctx.handle(message)

    def close(self) -> None:
        self.stack.close()


DLQ = MutableMapping[bytes, Tuple[M, str]]

Matcher = Callable[[M], bool]

Handler = Callable[[M, "HandlingContext[M]"], None]


class ProcessingContext(Generic[M]):
    def __init__(
        self, message_cls: Type[M], adapter: Adapter[M], processor: "Processor[M]"
    ) -> None:
        self.state = State()
        self.message_cls = message_cls
        self.adapter = adapter
        self.processor = processor

    def ack(self, message: M) -> None:
        self.adapter.ack(message)

    def nack(self, message: M) -> None:
        self.adapter.nack(message)

    def handle(self, message: M) -> None:
        matching_handlers = []
        for (matcher, handler) in self.processor.handlers.keys():
            if matcher(message):
                logger.debug("matched %s for %s", handler, message)
                matching_handlers.append(handler)
            else:
                logger.debug("did not match %s for %s", handler, message)

        if len(matching_handlers) == 0:
            reason = "no matching handlers"
            if self.processor.dlq is not None:
                logger.warning(
                    "no matching handlers for %s "
                    "- acking and putting putting on dlq",
                    message,
                )
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
                    "multiple matching handlers for %s "
                    "- acking and putting message on dlq",
                    message,
                )
                self.processor.dlq[message.message_id] = (message, reason)
                self.ack(message)
                return
            logger.critical(
                "multiple matching handlers for %s and no dlq configured - crashing",
                message,
            )
            raise RuntimeError("multiple matching handlers")

        (sole_matching_handler,) = matching_handlers
        logger.debug("calling %s", sole_matching_handler)
        try:
            with self.handling_context(message) as handling_context:
                sole_matching_handler(message, handling_context)
        except Exception as e:
            if self.processor.dlq is not None:
                reason = str(e)
                self.processor.dlq[message.message_id] = (message, reason)
                logger.warning(
                    "handler %s raised exception %s on message %s "
                    "- acking and putting message on dlq",
                    sole_matching_handler,
                    e,
                    message,
                    exc_info=True,
                )
                self.ack(message)
            else:
                logger.critical(
                    "handler %s raised exception %s on"
                    " message % and no dlq configured - crashing",
                    sole_matching_handler,
                    e,
                    message,
                    exc_info=True,
                )
                raise

    @contextmanager
    def handling_context(self, message: M) -> Iterator["HandlingContext[M]"]:
        """Enter the handling context, including calling hooks."""
        handling_context = HandlingContext(message, self)
        for hook in self.processor.hooks.before_handling:
            hook(self, handling_context)
        try:
            yield handling_context
        finally:
            for hook in self.processor.hooks.after_handling:
                hook(self, handling_context)


class HandlingContext(Generic[M]):
    def __init__(self, message: M, processing_ctx: ProcessingContext[M]) -> None:
        self.state = State()
        self.message = message
        self.processing_ctx = processing_ctx

    def ack(self) -> None:
        self.processing_ctx.ack(self.message)

    def nack(self) -> None:
        self.processing_ctx.nack(self.message)


ProcessingHook = Callable[[ProcessingContext[M]], None]

HandlingHook = Callable[[ProcessingContext[M], HandlingContext[M]], None]


@dataclass
class ProcessorHooks(Generic[M]):
    before_processing: MutableSequence[ProcessingHook[M]]
    after_processing: MutableSequence[ProcessingHook[M]]
    before_handling: MutableSequence[HandlingHook[M]]
    after_handling: MutableSequence[HandlingHook[M]]


class Processor(Generic[M]):
    def __init__(self) -> None:
        self.matchers: Set[Matcher[M]] = set()
        self.handlers: MutableMapping[Tuple[Matcher[M], Handler[M]], None] = {}
        self.dlq: Optional[DLQ[M]] = None
        self.hooks: ProcessorHooks[M] = ProcessorHooks([], [], [], [])

    def handle_for(self, matcher: Matcher[M]) -> Callable[[Handler[M]], None]:
        def wrapper(fn: Handler[M]) -> None:
            if matcher in self.matchers:
                (fn1,) = [h for (m, h) in self.handlers if m == matcher]
                raise RuntimeError(
                    f"two handlers with the same matcher: {fn} and {fn1} share {matcher}"
                )
            else:
                self.matchers.add(matcher)
            self.handlers[(matcher, fn)] = None

        return wrapper

    def before_processing(self, hook: ProcessingHook[M]) -> None:
        self.hooks.before_processing.append(hook)

    def after_processing(self, hook: ProcessingHook[M]) -> None:
        self.hooks.after_processing.append(hook)

    def before_handling(self, hook: HandlingHook[M]) -> None:
        self.hooks.before_handling.append(hook)

    def after_handling(self, hook: HandlingHook[M]) -> None:
        self.hooks.after_handling.append(hook)

    def set_dlq(self, dlq: DLQ[M]) -> None:
        self.dlq = dlq

    @contextmanager
    def context(
        self, message_cls: Type[M], adapter: Adapter[M]
    ) -> Iterator[ProcessingContext[M]]:
        """Enter the processing context, including calling hooks."""
        processing_ctx = ProcessingContext(message_cls, adapter, self)
        for hook in self.hooks.before_processing:
            hook(processing_ctx)
        try:
            yield processing_ctx
        finally:
            # Ensure that after hooks are still called in the case of an
            # uncaught exception
            for hook in self.hooks.after_processing:
                hook(processing_ctx)

    @contextmanager
    def test_client(self) -> Iterator[TestAdapter[M]]:
        with closing(TestAdapter(self)) as adapter:
            yield adapter

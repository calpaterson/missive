from typing import Callable, Sequence


class Matcher:
    ...


class Message:
    ...


class TestMessage(Message):
    ...


class Adapter:
    ...


class StdinAdapter(Adapter):
    ...


class TestClient:
    def __init__(self, processor: "Processor"):
        self.processor = processor

    def send(self, message: Message) -> None:
        ...


class Processor:
    def run(self, adapter: Adapter):
        ...

    def handler(self, matchers: Sequence) -> Callable:
        def wrapper(fn) -> None:
            ...

        return wrapper

    def test_client(self) -> TestClient:
        return TestClient(self)

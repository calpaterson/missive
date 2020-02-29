from typing import Tuple, MutableSequence, Type

import flask

from ..missive import Adapter, Processor, M


class WSGIAdapter(Adapter[M]):
    def __init__(self, message_cls: Type[M], processor: Processor[M]) -> None:
        self.processor = processor
        self.message_cls = message_cls

        self.app = flask.Flask("missive")
        self.acked: MutableSequence[M] = []
        self.nacked: MutableSequence[M] = []

        @self.app.route("/", methods=["POST"])
        def web_handler() -> Tuple[str, int]:
            message = self.message_cls(flask.request.data)
            with processor.handling_context(self.message_cls, self) as ctx:
                ctx.handle(message)
                # FIXME: should check whether acked or nacked first
                return "", 200

    def ack(self, message: M) -> None:
        self.acked.append(message)

    def nack(self, message: M) -> None:
        self.nacked.append(message)

    def run(self) -> None:
        self.app.run()

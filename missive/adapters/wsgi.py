from typing import Tuple, MutableSequence

import flask

from ..missive import Adapter, Processor, GenericMessage


class WSGIAdapter(Adapter[GenericMessage]):
    def __init__(self, processor: Processor[GenericMessage]) -> None:
        self.processor = processor

        self.app = flask.Flask("missive")
        self.acked: MutableSequence[GenericMessage] = []
        self.nacked: MutableSequence[GenericMessage] = []

        @self.app.route("/", methods=["POST"])
        def web_handler() -> Tuple[str, int]:
            message = GenericMessage(flask.request.data)
            with processor.handling_context(self) as ctx:
                ctx.handle(message)
                # FIXME: should check whether acked or nacked first
                return "", 200

    def ack(self, message: GenericMessage) -> None:
        self.acked.append(message)

    def nack(self, message: GenericMessage) -> None:
        self.nacked.append(message)

    def run(self) -> None:
        self.app.run()

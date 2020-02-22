from typing import Tuple

import flask

from ..missive import Adapter, Processor
from ..messages import GenericMessage


class WSGIAdapter(Adapter):
    def __init__(self, processor: Processor) -> None:
        self.processor = processor

        self.app = flask.Flask("missive")

        @self.app.route("/", methods=["POST"])
        def web_handler() -> Tuple[str, int]:
            message = GenericMessage(flask.request.data)
            self.processor.handle(message)
            # FIXME: should check whether acked or nacked first
            return "", 200

    def run(self) -> None:
        self.app.run()

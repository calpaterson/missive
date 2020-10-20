from typing import Tuple, MutableSequence, Type

import flask

from ..missive import Adapter, Processor, M


class WSGIAdapter(Adapter[M]):
    """Adapts a Processor to Python's Web Server Gateway Interface.

    :param message_cls: The message class to pass to the processor
    :param processor: The underlying processor

    """

    def __init__(self, message_cls: Type[M], processor: Processor[M]) -> None:
        self.processor = processor
        self.message_cls = message_cls

        #: The wsgi application object - reference this in your WSGI server config
        self.app: flask.Flask = flask.Flask("missive")

        self.acked: MutableSequence[M] = []
        self.nacked: MutableSequence[M] = []

        @self.app.route("/", methods=["POST"])
        def web_handler() -> Tuple[str, int]:
            message = self.message_cls(flask.request.data)
            with processor.context(self.message_cls, self) as ctx:
                ctx.handle(message)
                if message in self.acked:
                    self.acked.remove(message)
                    return flask.jsonify({"result": "ack"}), 200
                else:
                    self.nacked.remove(message)
                    return flask.jsonify({"result": "nack"}), 500

    def ack(self, message: M) -> None:
        self.acked.append(message)

    def nack(self, message: M) -> None:
        self.nacked.append(message)

    def run(self) -> None:
        """Run the wsgi application directly using Flask's builtin server.

        """
        self.app.run()

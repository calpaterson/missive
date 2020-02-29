from typing import cast

import missive as m
from missive.messages import GenericMessage
from missive.adapters.wsgi import WSGIAdapter


def test_acking():
    processor: m.Processor[GenericMessage] = m.Processor()

    message_received = None

    @processor.handle_for([])
    def flip_bit(message: m.Message):
        nonlocal message_received
        message_received = message
        message.ack()

    adapted_processor = WSGIAdapter(processor)

    with adapted_processor.app.test_client() as test_client:
        test_client.post("/", data=b"hello")

    assert cast(m.Message, message_received).raw_data == b"hello"

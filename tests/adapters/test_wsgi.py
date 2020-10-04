from typing import cast

import missive as m
from missive.adapters.wsgi import WSGIAdapter

from ..matchers import always


def test_acking():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    message_received = None

    @processor.handle_for(always)
    def flip_bit(message: m.GenericMessage, ctx: m.HandlingContext[m.GenericMessage]):
        nonlocal message_received
        message_received = message
        ctx.ack(message)

    adapted_processor = WSGIAdapter(m.GenericMessage, processor)

    with adapted_processor.app.test_client() as test_client:
        response = test_client.post("/", data=b"hello")

    assert response.status_code == 200
    assert response.json == {"result": "ack"}
    assert cast(m.Message, message_received).raw_data == b"hello"


def test_nacking():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    message_received = None

    @processor.handle_for(always)
    def flip_bit(message: m.GenericMessage, ctx: m.HandlingContext[m.GenericMessage]):
        nonlocal message_received
        message_received = message
        ctx.nack(message)

    adapted_processor = WSGIAdapter(m.GenericMessage, processor)

    with adapted_processor.app.test_client() as test_client:
        response = test_client.post("/", data=b"hello")

    assert response.status_code == 500
    assert response.json == {"result": "nack"}
    assert cast(m.Message, message_received).raw_data == b"hello"

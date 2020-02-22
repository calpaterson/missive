import missive as m
from missive.adapters.wsgi import WSGIAdapter


def test_acking():
    processor = m.Processor()

    message_received = None

    @processor.handle_for([])
    def flip_bit(message: m.Message):
        nonlocal message_received
        message_received = message
        message.ack()

    adapted_processor = WSGIAdapter(processor)

    with adapted_processor.app.test_client() as test_client:
        test_client.post("/", data=b"hello")

    assert message_received.data == b"hello"

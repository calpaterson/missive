from typing import List, Tuple, Dict

import missive as m


def test_no_dlq_required():
    dlq: Dict = {}

    processor: m.Processor[m.GenericMessage] = m.Processor()
    processor.set_dlq(dlq)

    flag = False

    @processor.handle_for([])
    def flip_bit(
        message: m.GenericMessage, ctx: m.HandlingContext[m.GenericMessage]
    ) -> None:
        nonlocal flag
        flag = True
        ctx.ack(message)

    test_client = processor.test_client()

    blank_message = m.GenericMessage(b"")

    test_client.send(blank_message)

    assert flag
    assert blank_message in test_client.acked


def test_no_matching_handler():
    dlq: Dict = {}

    processor: m.Processor[m.GenericMessage] = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for((lambda m: False,))
    def non_matching_handler(message, ctx):
        assert False

    test_client = processor.test_client()

    blank_message = m.GenericMessage(b"")

    test_client.send(blank_message)

    assert blank_message in test_client.acked
    assert list(dlq.values()) == [(blank_message, "no matching handlers")]


def test_multiple_matching_handlers():
    dlq: Dict = {}

    processor: m.Processor[m.GenericMessage] = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message, ctx):
        ctx.ack(message)

    @processor.handle_for((lambda m: True,))
    def another_matching_handler(message, ctx):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.GenericMessage(b"")

    test_client.send(blank_message)

    assert blank_message in test_client.acked
    assert list(dlq.values()) == [(blank_message, "multiple matching handlers")]

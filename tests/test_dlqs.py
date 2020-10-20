from typing import List, Tuple, Dict

import missive as m

from .matchers import always, never


def test_no_dlq_required():
    """Test the happy path where the DLQ is never used"""
    dlq: Dict = {}

    processor: m.Processor[m.RawMessage] = m.Processor()
    processor.set_dlq(dlq)

    flag = False

    @processor.handle_for(always)
    def flip_bit(message: m.RawMessage, ctx: m.ProcessingContext[m.RawMessage]) -> None:
        nonlocal flag
        flag = True
        ctx.ack(message)

    test_client = processor.test_client()

    blank_message = m.RawMessage(b"")

    test_client.send(blank_message)

    assert flag
    assert blank_message in test_client.acked


def test_no_matching_handler():
    """Messages for which no handler matches should be written to the DLQ"""
    dlq: Dict = {}

    processor: m.Processor[m.RawMessage] = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for(never)
    def non_matching_handler(message, ctx):
        assert False

    test_client = processor.test_client()

    blank_message = m.RawMessage(b"")

    test_client.send(blank_message)

    assert blank_message in test_client.acked
    assert list(dlq.values()) == [(blank_message, "no matching handlers")]


def test_multiple_matching_handlers():
    dlq: Dict = {}

    processor: m.Processor[m.RawMessage] = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for(always)
    def a_matching_handler(message, ctx):
        ctx.ack(message)

    @processor.handle_for(lambda m: True)
    def another_matching_handler(message, ctx):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.RawMessage(b"")

    test_client.send(blank_message)

    assert blank_message in test_client.acked
    assert list(dlq.values()) == [(blank_message, "multiple matching handlers")]

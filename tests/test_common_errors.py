import missive

import pytest

from .matchers import always


def test_exception_raised_no_dlq():
    """If an exception is raised and there's no DLQ, the proc should crash,
    (without acking)."""

    proc: missive.Processor[missive.RawMessage] = missive.Processor()

    @proc.handle_for(always)
    def crash(message, ctx):
        raise RuntimeError("bad bytes!")

    test_client = proc.test_client()
    blank_message = missive.RawMessage(b"")
    with pytest.raises(RuntimeError):
        test_client.send(blank_message)


def test_exception_raised_with_a_dlq():
    """If an exception is raised and there's a DLQ, it's written to the DLQ,
    acked and the processor gets on with it's life."""
    proc: missive.Processor[missive.RawMessage] = missive.Processor()
    dlq: missive.DLQ = {}
    proc.set_dlq(dlq)

    @proc.handle_for(always)
    def crash(message, ctx):
        raise RuntimeError("bad bytes!")

    test_client = proc.test_client()
    blank_message = missive.RawMessage(b"")
    test_client.send(blank_message)
    assert dlq == {blank_message.message_id: (blank_message, "bad bytes!")}
    assert blank_message in test_client.acked


@pytest.mark.xfail(reason="not implemented")
def test_no_ack():
    assert False


def test_two_handlers_with_the_same_matcher():
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    @processor.handle_for(always)
    def handler_1(message, ctx):
        ctx.ack(message)

    with pytest.raises(RuntimeError):

        @processor.handle_for(always)
        def handler_2(message, ctx):
            ctx.ack(message)

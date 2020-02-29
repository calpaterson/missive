import pytest

import missive as m


def test_one_matching_handler():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    flag = False

    @processor.handle_for([])
    def flip_bit(
        message: m.GenericMessage, ctx: m.HandlingContext[m.GenericMessage]
    ) -> None:
        nonlocal flag
        flag = True
        ctx.ack(message)

    test_client = processor.test_client()

    blank_message = m.GenericMessage()

    test_client.send(blank_message)

    assert flag
    assert blank_message in test_client.acked


def test_no_matching_handler():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    @processor.handle_for((lambda m: False,))
    def non_matching_handler(message, ctx):
        assert False

    test_client = processor.test_client()

    blank_message = m.GenericMessage()

    with pytest.raises(RuntimeError):
        test_client.send(blank_message)

    assert blank_message not in test_client.acked


def test_multiple_matching_handlers():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message, ctx):
        message.ack()

    @processor.handle_for((lambda m: True,))
    def another_matching_handler(message, ctx):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.GenericMessage()

    with pytest.raises(RuntimeError):
        test_client.send(blank_message)

    assert blank_message not in test_client.acked


def test_one_matching_handler_among_multiple():
    processor: m.Processor[m.GenericMessage] = m.Processor()

    flag = False

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message, ctx):
        nonlocal flag
        flag = True
        ctx.ack(message)

    @processor.handle_for((lambda m: False,))
    def another_matching_handler(message, ctx):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.GenericMessage()

    test_client.send(blank_message)

    assert flag
    assert blank_message in test_client.acked

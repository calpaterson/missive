import pytest

import missive as m


def test_one_matching_handler():
    processor: m.Processor[m.TestMessage] = m.Processor()

    flag = False

    @processor.handle_for([])
    def flip_bit(message: m.Message) -> None:
        nonlocal flag
        flag = True
        message.ack()

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert flag
    assert blank_message.acked


def test_no_matching_handler():
    processor: m.Processor[m.TestMessage] = m.Processor()

    @processor.handle_for((lambda m: False,))
    def non_matching_handler(message):
        assert False

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    with pytest.raises(RuntimeError):
        test_client.send(blank_message)

    assert not blank_message.acked


def test_multiple_matching_handlers():
    processor: m.Processor[m.TestMessage] = m.Processor()

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message):
        message.ack()

    @processor.handle_for((lambda m: True,))
    def another_matching_handler(message):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    with pytest.raises(RuntimeError):
        test_client.send(blank_message)

    assert not blank_message.acked


def test_one_matching_handler_among_multiple():
    processor: m.Processor[m.TestMessage] = m.Processor()

    flag = False

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message):
        nonlocal flag
        flag = True
        message.ack()

    @processor.handle_for((lambda m: False,))
    def another_matching_handler(message):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert flag
    assert blank_message.acked

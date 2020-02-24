from typing import List, Tuple

import pytest

import missive as m


def test_no_dlq_required():
    dlq = {}

    processor = m.Processor()
    processor.set_dlq(dlq)

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
    dlq = {}

    processor = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for((lambda m: False,))
    def non_matching_handler(message):
        assert False

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert blank_message.acked
    assert list(dlq.values()) == [(blank_message, "no matching handlers")]


def test_multiple_matching_handlers():
    dlq = {}

    processor = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for((lambda m: True,))
    def a_matching_handler(message):
        message.ack()

    @processor.handle_for((lambda m: True,))
    def another_matching_handler(message):
        message.ack()

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert blank_message.acked
    assert list(dlq.values()) == [(blank_message, "multiple matching handlers")]

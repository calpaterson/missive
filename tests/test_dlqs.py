from typing import List, Tuple

import pytest

import missive as m


class ListDLQ(m.DLQ):
    def __init__(self):
        self.messages: List[Tuple[m.Message, str]] = []

    def add(self, message: m.Message, reason: str):
        self.messages.append((message, reason))


def test_no_dlq_required():
    dlq = ListDLQ()

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
    dlq = ListDLQ()

    processor = m.Processor()
    processor.set_dlq(dlq)

    @processor.handle_for((lambda m: False,))
    def non_matching_handler(message):
        assert False

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert blank_message.acked
    assert dlq.messages == [(blank_message, "no matching handlers")]


def test_multiple_matching_handlers():
    dlq = ListDLQ()

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
    assert dlq.messages == [(blank_message, "multiple matching handlers")]

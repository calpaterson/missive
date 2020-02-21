import missive as m

import pytest


@pytest.mark.xfail()
def test_simple():
    processor = m.Processor()

    flag = False

    @processor.handler([])
    def flip_bit(message: m.Message) -> None:
        flag = True

    test_client = processor.test_client()

    blank_message = m.TestMessage()

    test_client.send(blank_message)

    assert flag

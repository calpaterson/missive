import missive

import pytest

from .matchers import always


@pytest.mark.xfail(reason="not implemented")
def test_exception_raised():
    assert False


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

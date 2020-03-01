import pytest


@pytest.mark.xfail(reason="not implemented")
def test_ctrl_c():
    assert False


@pytest.mark.xfail(reason="not implemented")
def test_sigterm():
    assert False

import pytest

from missive.state import State


def test_getting_and_setting():
    state = State()
    state.foo = 1
    assert state.foo == 1


def test_doesnt_exist():
    state = State()
    with pytest.raises(AttributeError):
        state.foo + 1


def test_deleting():
    state = State()
    state.foo = 1
    del state.foo

    with pytest.raises(AttributeError):
        state.foo + 1

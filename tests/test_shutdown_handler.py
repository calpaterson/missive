import signal
from unittest.mock import Mock

import pytest

from missive.shutdown_handler import ShutdownHandler


@pytest.fixture(scope="function")
def reset_signals():
    relevant_signals = {signal.SIGTERM, signal.SIGINT}
    # Record the current signals...
    old_handlers = {
        relevant_signal: signal.getsignal(relevant_signal)
        for relevant_signal in relevant_signals
    }
    yield
    # ...and replace them afterwards
    for relevant_signal in relevant_signals:
        signal.signal(relevant_signal, old_handlers[relevant_signal])


@pytest.mark.parametrize("sig", (signal.SIGINT, signal.SIGTERM))
def test_signal_handling(sig):
    sh = ShutdownHandler()
    sh.enable()
    signal.getsignal(sig)(sig, None)  # type: ignore
    assert sh.should_exit()


@pytest.mark.parametrize("sig", (signal.SIGINT, signal.SIGTERM))
def test_callback(sig):
    called_with = None

    def cb(sig):
        nonlocal called_with
        called_with = sig

    sh = ShutdownHandler(callback=cb)
    sh.enable()
    signal.getsignal(sig)(sig, None)  # type: ignore
    assert called_with == sig

from typing import Any

import json

import missive

import pytest


class FakeConnection:
    """A simple stand in for something stateful - eg SQL connection."""

    def __init__(self):
        self.status = "idle"
        self.opens = 0
        self.commits = 0

    def open(self):
        assert self.status == "idle"
        self.status = "open"
        self.opens += 1

    def commit(self):
        assert self.status == "open"
        self.status = "idle"
        self.commits = 0

    def close(self):
        assert self.status == "idle"
        self.status = "closed"


class TypeMatcher:
    def __init__(self, type_: str):
        self.type_ = type_

    def __call__(self, message: missive.JSONMessage) -> bool:
        type_: str = message.get_json()["type"]
        return type_ == self.type_


def to_json_message(o: Any) -> missive.JSONMessage:
    return missive.JSONMessage(json.dumps(o).encode("utf-8"))


def init_proc(pool) -> missive.Processor[missive.JSONMessage]:
    proc: missive.Processor[missive.JSONMessage] = missive.Processor()

    @proc.before_processing
    def create_session(proc_ctx: missive.ProcessingContext[missive.JSONMessage]):
        # pretend connection pool
        proc_ctx.state.pool = pool

    @proc.before_handling
    def create_connection(
        proc_ctx: missive.ProcessingContext,
        handling_ctx: missive.HandlingContext[missive.JSONMessage],
    ):
        handling_ctx.state.conn = proc_ctx.state.pool.pop()
        handling_ctx.state.conn.open()

    @proc.handle_for(TypeMatcher("happy"))
    def happy_handler(
        message: missive.JSONMessage,
        handling_ctx: missive.HandlingContext[missive.JSONMessage],
    ):
        handling_ctx.ack()

    @proc.after_handling
    def return_connection(proc_ctx, handling_ctx):
        handling_ctx.state.conn.commit()
        proc_ctx.state.pool.append(handling_ctx.state.conn)

    @proc.after_processing
    def close_session(proc_ctx):
        for conn in proc_ctx.state.pool:
            conn.close()

    return proc


def test_no_failures():
    pool = [FakeConnection() for _ in range(3)]

    proc = init_proc(pool)
    proc.test_client()
    with proc.test_client() as tc:
        tc.send(to_json_message({"type": "happy"}))

    statuses = [conn.status for conn in pool]
    assert statuses == ["closed", "closed", "closed"]


def test_handler_exception():
    pool = [FakeConnection() for _ in range(3)]

    proc = init_proc(pool)

    @proc.handle_for(TypeMatcher("handler_exception"))
    def problem_handler(m, ctx):
        raise RuntimeError("something bad happened")

    with proc.test_client() as tc:
        with pytest.raises(RuntimeError):
            tc.send(to_json_message({"type": "handler_exception"}))

    statuses = [conn.status for conn in pool]
    assert statuses == ["closed", "closed", "closed"]


@pytest.mark.parametrize("hook_name", ["before_processing", "after_processing"])
def test_crash_when_processing_hooks_raise(hook_name):
    """When a processing hook raises an exception, we should crash regardless
    of whether a DLQ is set or not as this is not related to a message and is
    probably unrecoverable.

    """
    proc = init_proc([FakeConnection()])

    hook = getattr(proc, hook_name)

    @hook
    def raise_exc(p_ctx: missive.ProcessingContext):
        raise RuntimeError("something wrong in setup")

    with pytest.raises(RuntimeError):
        with proc.test_client() as tc:
            tc.send(to_json_message({"type": "happy"}))


@pytest.mark.parametrize("hook_name", ["before_handling", "after_handling"])
def test_dlq_used_when_handling_hooks_raise(hook_name):
    """When a handling hook raises an exception, the message should follow the
    normal DLQ policy as it's probably a message specific error."""
    proc = init_proc([FakeConnection()])
    dlq: missive.DLQ = {}
    proc.set_dlq(dlq)

    hook = getattr(proc, hook_name)

    @hook
    def raise_exc_hook(p_ctx, h_ctx):
        raise RuntimeError("bad bytes")

    with proc.test_client() as tc:
        tc.send(to_json_message({"type": "happy"}))

    assert len(dlq) == 1


@pytest.mark.parametrize("hook_name", ["before_handling", "after_handling"])
def test_handling_hooks_exc_propagates_when_no_dlq(hook_name):
    """When there's no DLQ, handling hook exceptions crash the processor"""
    proc = init_proc([FakeConnection()])

    hook = getattr(proc, hook_name)

    @hook
    def raise_exc_hook(p_ctx, h_ctx):
        raise RuntimeError("bad bytes")

    with proc.test_client() as tc:
        with pytest.raises(RuntimeError):
            tc.send(to_json_message({"type": "happy"}))

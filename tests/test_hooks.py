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
    tc = proc.test_client()
    tc.send(missive.JSONMessage(json.dumps({"type": "happy"}).encode("utf-8")))
    tc.close()

    statuses = [conn.status for conn in pool]
    assert statuses == ["closed", "closed", "closed"]


def test_handler_exception():
    pool = [FakeConnection() for _ in range(3)]

    proc = init_proc(pool)

    @proc.handle_for(TypeMatcher("handler_exception"))
    def problem_handler(m, ctx):
        raise RuntimeError("something bad happened")

    proc.test_client()
    tc = proc.test_client()
    with pytest.raises(RuntimeError):
        tc.send(
            missive.JSONMessage(
                json.dumps({"type": "handler_exception"}).encode("utf-8")
            )
        )

    tc.close()

    statuses = [conn.status for conn in pool]
    assert statuses == ["closed", "closed", "closed"]

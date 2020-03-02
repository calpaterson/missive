import time
import threading
import json

import redis
import pytest

import missive
from missive.adapters.redis import RedisPubSubAdapter


@pytest.fixture
def redis_client():
    yield redis.Redis()


def test_message_receipt(redis_client):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for([])
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RedisPubSubAdapter(missive.JSONMessage, processor, ["test-channel"])

    thread = threading.Thread(target=adapted.run)
    thread.start()

    while adapted.thread is None:
        time.sleep(0)

    test_event = {"test-event": True}

    redis_client.publish("test-channel", json.dumps(test_event))

    while adapted.thread.is_alive():
        time.sleep(0)

    assert flag == test_event

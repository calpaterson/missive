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
    import time

    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for([])
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapter.shutdown_handler.set_flag()

    adapter = RedisPubSubAdapter(missive.JSONMessage, processor, ["test-channel"])

    thread = threading.Thread(target=adapter.run)
    thread.start()

    time.sleep(0.1)

    test_event = {"test-event": True}

    redis_client.publish("test-channel", json.dumps(test_event))
    time.sleep(0.1)

    assert flag == test_event
    thread.join()

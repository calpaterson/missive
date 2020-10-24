import time
import threading
import json

import redis
import pytest

import missive
from missive.adapters.redis import RedisPubSubAdapter

from ..matchers import always


@pytest.fixture
def redis_client():
    yield redis.Redis()


def test_message_receipt(redis_client):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for(always)
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack()
        adapted.shutdown_handler.set_flag()

    adapted = RedisPubSubAdapter(missive.JSONMessage, processor, ["test-channel"])

    thread = threading.Thread(target=adapted.run)
    thread.start()

    while adapted.thread is None:
        time.sleep(0.01)

    test_event = {"test-event": True}

    redis_client.publish("test-channel", json.dumps(test_event))

    adapted.thread.join(1)

    assert flag == test_event

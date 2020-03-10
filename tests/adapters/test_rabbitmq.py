import threading
import random
import string
import contextlib
import json
from unittest.mock import patch, Mock

import kombu
import pytest

import missive
from missive import shutdown_handler

from missive.adapters.rabbitmq import RabbitMQAdapter


@pytest.fixture(scope="module")
def channel():
    with kombu.Connection() as conn:
        with conn.channel() as channel:
            yield channel


@pytest.fixture(scope="function")
def random_queue(channel):
    postfix = "".join(random.choice(string.ascii_letters) for _ in range(5))
    queue_name = "test-%s" % postfix

    queue = kombu.Queue(queue_name, auto_delete=True)
    bound_queue = queue(channel)
    bound_queue.declare()
    yield bound_queue


@patch.object(shutdown_handler, "signal", Mock())
def test_message_receipt(channel, random_queue):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for([])
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(missive.JSONMessage, processor, random_queue.name)

    test_event = {"test-event": True}
    producer = kombu.Producer(channel)

    producer.publish(
        json.dumps(test_event).encode("utf-8"), routing_key=random_queue.name
    )

    thread = threading.Thread(target=adapted.run)
    thread.start()
    thread.join()

    assert flag == test_event

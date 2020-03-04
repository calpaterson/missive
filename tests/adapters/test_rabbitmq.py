import threading
import random
import string
import contextlib
import json
from unittest.mock import patch, Mock

import pytest
import librabbitmq

import missive
from missive import shutdown_handler

from missive.adapters.rabbitmq import RabbitMQAdapter


@pytest.fixture(scope="module")
def rabbitmq_channel():
    with contextlib.closing(librabbitmq.Connection()) as connection:
        with contextlib.closing(connection.channel()) as channel:
            yield channel


@pytest.fixture(scope="function")
def random_queue(rabbitmq_channel):
    postfix = "".join(random.choice(string.ascii_letters) for _ in range(5))
    queue_name = "test-%s" % postfix
    rabbitmq_channel.queue_declare(queue_name, auto_delete=True)
    yield queue_name


@patch.object(shutdown_handler, "signal", Mock())
def test_message_receipt(rabbitmq_channel, random_queue):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for([])
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(missive.JSONMessage, processor, random_queue)

    test_event = {"test-event": True}

    rabbitmq_channel.basic_publish(
        exchange="",
        routing_key=random_queue,
        body=json.dumps(test_event).encode("utf-8"),
    )

    thread = threading.Thread(target=adapted.run)
    thread.start()
    thread.join()

    assert flag == test_event

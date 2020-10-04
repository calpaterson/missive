import threading
import random
import string
import json
from unittest.mock import patch, Mock

import kombu
import pytest

import missive
from missive import shutdown_handler
from missive.adapters.rabbitmq import RabbitMQAdapter

from ..matchers import always

RABBITMQ_URL = "amqp:///missive-test"


@pytest.fixture(scope="module")
def connection(scope="module"):
    with kombu.Connection(RABBITMQ_URL) as connection:
        yield connection


@pytest.fixture(scope="module")
def channel(connection):
    with connection.channel() as channel:
        yield channel


def make_random_queue(channel):
    postfix = "".join(random.choice(string.ascii_letters) for _ in range(5))
    queue_name = "test-%s" % postfix

    queue = kombu.Queue(queue_name, channel=channel)
    return queue


@pytest.fixture(scope="function")
def random_queue(channel):
    queue = make_random_queue(channel)
    queue.declare()
    yield queue
    queue.delete()


@patch.object(shutdown_handler, "signal", Mock())
def test_message_receipt(channel, random_queue):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for(always)
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(
        missive.JSONMessage,
        processor,
        [random_queue.name],
        url_or_conn=RABBITMQ_URL,
        disable_shutdown_handler=True,
    )

    test_event = {"test-event": True}
    producer = kombu.Producer(channel)

    producer.publish(
        json.dumps(test_event).encode("utf-8"), routing_key=random_queue.name
    )

    thread = threading.Thread(target=adapted.run)
    thread.start()
    thread.join()

    assert flag == test_event

    # Assert nothing left on the queue
    assert random_queue.get() is None


def test_passing_a_conn(channel, random_queue, connection):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for(always)
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(
        missive.JSONMessage,
        processor,
        [random_queue.name],
        url_or_conn=connection,
        disable_shutdown_handler=True,
    )

    test_event = {"test-event": True}
    producer = kombu.Producer(channel)

    producer.publish(
        json.dumps(test_event).encode("utf-8"), routing_key=random_queue.name
    )

    thread = threading.Thread(target=adapted.run)
    thread.start()
    thread.join()

    assert flag == test_event

    # Assert nothing left on the queue
    assert random_queue.get() is None


def test_receipt_from_multiple_queues(channel):
    q1 = make_random_queue(channel)
    q1.declare()
    q2 = make_random_queue(channel)
    q2.declare()

    messages = set()

    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    @processor.handle_for(always)
    def catch_all(message, ctx):
        messages.add(message.get_json()["n"])
        ctx.ack(message)
        if len(messages) >= 2:
            adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(
        missive.JSONMessage,
        processor,
        [q1.name, q2.name],
        url_or_conn=RABBITMQ_URL,
        disable_shutdown_handler=True,
    )

    producer = kombu.Producer(channel)
    producer.publish(json.dumps({"n": 1}).encode("utf-8"), routing_key=q1.name)
    producer.publish(json.dumps({"n": 2}).encode("utf-8"), routing_key=q2.name)

    thread = threading.Thread(target=adapted.run)
    thread.start()
    thread.join()

    assert len(messages) == 2

    q1.delete()
    q2.delete()

import threading
import time
import contextlib
import json

import pika
import pytest

import missive

from missive.adapters.rabbitmq import RabbitMQAdapter


@pytest.fixture(scope="module")
def rabbitmq_client():
    with contextlib.closing(pika.BlockingConnection()) as connection:
        yield connection


def test_message_receipt(rabbitmq_client):
    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    flag = False

    @processor.handle_for([])
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = RabbitMQAdapter(missive.JSONMessage, processor)

    channel = rabbitmq_client.channel()
    channel.queue_declare("test")

    test_event = {"test-event": True}

    channel.basic_publish(
        exchange="", routing_key="test", body=json.dumps(test_event).encode("utf-8")
    )

    thread = threading.Thread(target=adapted.run)
    thread.start()

    time.sleep(3)
    # while adapted.thread is None:
    #     time.sleep(0)

    # while adapted.thread.is_alive():
    #     time.sleep(0)

    assert flag == test_event

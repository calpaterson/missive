import json
import threading
import time
import os

import missive
from missive.adapters.stdin import StdinAdapter

from ..matchers import always


def test_from_file():
    r_pipe, w_pipe = os.pipe()
    r_fl, w_fl = os.fdopen(r_pipe, mode="rb"), os.fdopen(w_pipe, mode="wb")

    flag = False

    processor: missive.Processor[missive.JSONMessage] = missive.Processor()

    @processor.handle_for(always)
    def catch_all(message, ctx):
        nonlocal flag
        flag = message.get_json()
        ctx.ack(message)
        adapted.shutdown_handler.set_flag()

    adapted = StdinAdapter(missive.JSONMessage, processor, r_fl)
    thread = threading.Thread(target=adapted.run)
    thread.start()

    test_event = {"test-event": True}

    w_fl.write(json.dumps({"test-event": True}).encode("utf-8"))
    w_fl.write(b"\n")
    w_fl.flush()

    thread.join()

    assert flag == test_event

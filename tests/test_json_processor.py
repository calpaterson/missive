import json
from typing import cast, Dict

import missive

processor: missive.Processor[missive.JSONMessage] = missive.Processor()

db = []


@processor.handle_for([lambda m: cast(str, cast(Dict, m.get_json())["flag"]) == "a"])
def handle_as(message):
    db.append(message.get_json())
    message.ack()


def test_json():
    tc = processor.test_client()

    body = {"flag": "a"}

    tc.send(missive.JSONMessage(raw_data=json.dumps(body).encode("utf-8")))

    assert db == [body]

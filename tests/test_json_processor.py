import json
from typing import cast, Dict

import missive

processor: missive.Processor[missive.JSONMessage] = missive.Processor()

db = []


@processor.handle_for(lambda m: cast(str, cast(Dict, m.get_json())["flag"]) == "a")
def handle_as(message, ctx):
    db.append(message.get_json())
    ctx.ack()


def test_json():
    with processor.test_client() as tc:
        body = {"flag": "a"}
        tc.send(missive.JSONMessage(json.dumps(body).encode("utf-8")))
        assert db == [body]

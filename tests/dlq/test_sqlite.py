import pytest
from datetime import datetime, timezone

from freezegun import freeze_time

from missive.messages import GenericMessage
from missive.dlq.sqlite import SQLiteDLQ


@pytest.fixture(scope="function")
def dlq():
    return SQLiteDLQ(connection_str=":memory:")


@freeze_time("2018-01-03")
def test_set_and_get(dlq):
    message = GenericMessage(raw_data="test")

    dlq[message.message_id] = (message, "no reason")

    assert dlq.oldest() == (
        message,
        "no reason",
        datetime(2018, 1, 3, tzinfo=timezone.utc),
    )


@freeze_time("2018-01-03")
def test_set_and_remove(dlq):
    message = GenericMessage(raw_data="test")

    dlq[message.message_id] = (message, "no reason")

    del dlq[message.message_id]

    assert len(dlq) == 0

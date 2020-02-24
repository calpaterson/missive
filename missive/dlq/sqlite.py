from datetime import datetime, timezone
from typing import Tuple
import sqlite3
import pickle

from ..missive import DLQ, Message

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    message_id BLOB PRIMARY KEY,
    message_bytes BLOB,
    reason TEXT,
    inserted TEXT
);"""

INSERT = """
INSERT INTO messages
(message_id, message_bytes, reason, inserted)
VALUES (?, ?, ?, ?);
"""

OLDEST = """
SELECT message_bytes, reason, inserted
FROM messages
ORDER BY inserted DESC
LIMIT 1;
"""


class SQLiteDLQ(DLQ):
    def __init__(self, connection_str: str):
        self.connection_str = connection_str
        self.db_handle = sqlite3.connect(connection_str)
        self.db_handle.execute(SCHEMA)

    def add(self, message: Message, reason: str) -> None:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.db_handle.execute(
            INSERT, (message.message_id.bytes, pickle.dumps(message), reason, now)
        )
        self.db_handle.commit()

    def remove(self, message: Message) -> None:
        ...

    def oldest(self) -> Tuple[Message, str, datetime]:
        ((message_pickle, reason, inserted_str),) = self.db_handle.execute(OLDEST)
        return (
            pickle.loads(message_pickle),
            reason,
            datetime.fromisoformat(inserted_str),
        )

    def __repr__(self) -> str:
        return "<SqliteDLQ '%s'>" % self.connection_str

from datetime import datetime, timezone
from typing import Tuple, Iterator
import sqlite3
import pickle

from ..missive import DLQ, Message, M

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

DELETE = """
DELETE FROM messages WHERE message_id = ?;
"""

OLDEST = """
SELECT message_bytes, reason, inserted
FROM messages
ORDER BY inserted DESC
LIMIT 1;
"""

LENGTH = """
SELECT count(*) from messages
"""


class SQLiteDLQ(DLQ[M]):
    def __init__(self, connection_str: str):
        # FIXME: Should have an option to emit whatever pragma is required for
        # WAL mode
        self.connection_str = connection_str
        self.db_handle = sqlite3.connect(connection_str)
        self.db_handle.execute(SCHEMA)

    def __setitem__(self, message_id: bytes, pair: Tuple[Message, str]) -> None:
        message, reason = pair
        now = datetime.utcnow().replace(tzinfo=timezone.utc)
        self.db_handle.execute(
            INSERT, (message.message_id, pickle.dumps(message), reason, now)
        )
        self.db_handle.commit()

    def __delitem__(self, message_id: bytes) -> None:
        self.db_handle.execute(DELETE, (message_id,))
        self.db_handle.commit()

    def __len__(self) -> int:
        rv: int = self.db_handle.execute(LENGTH).fetchall()[0][0]
        self.db_handle.commit()
        return rv

    def __getitem__(self, message_id: bytes) -> Tuple[M, str]:
        ...

    def __iter__(self) -> Iterator[bytes]:
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

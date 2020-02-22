from ..missive import DLQ, Message


class FileDQL(DLQ):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.buf = open(file_path, "ba", buffering=0)

    def add(self, message: Message, reason: str) -> None:
        output = message.data + b"," + reason.encode("utf-8") + b"\n"
        self.buf.write(output)

    def __repr__(self) -> str:
        return "<FileDQL %s>" % self.file_path

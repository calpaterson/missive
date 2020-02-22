from .missive import Message, logger


class GenericMessage(Message):
    def ack(self) -> None:
        logger.info("acked: %s", self)

    def nack(self) -> None:
        logger.info("nacked: %s", self)

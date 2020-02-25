import missive
from missive.messages import GenericMessage
from missive.adapters.stdin import StdinAdapter

processor = missive.Processor[GenericMessage]()


def is_greeting(message: GenericMessage) -> bool:
    return message.raw_data in [b"hello", b"goodbye"]


@processor.handle_for([is_greeting])
def match_greetings(message) -> None:
    if message.data == b"hello":
        print("hi there")
    if message.data == b"goodbye":
        print("bye then")
    message.ack()


@processor.handle_for([lambda m: not is_greeting(m)])
def otherwise(message):
    # don't respond
    message.ack()


adapted = StdinAdapter(processor)


if __name__ == "__main__":
    adapted.run()

import missive
from missive.adapters.stdin import StdinAdapter

processor = missive.Processor[missive.GenericMessage]()


def is_greeting(message: missive.GenericMessage) -> bool:
    return message.raw_data in [b"hello", b"goodbye"]


@processor.handle_for([is_greeting])
def match_greetings(message, ctx) -> None:
    if message.raw_data == b"hello":
        print("hi there")
    if message.raw_data == b"goodbye":
        print("bye then")
    ctx.ack(message)


@processor.handle_for([lambda m: not is_greeting(m)])
def otherwise(message, ctx):
    # don't respond
    ctx.ack(message)


adapted = StdinAdapter(missive.GenericMessage, processor)


if __name__ == "__main__":
    adapted.run()

import missive
from missive.adapters.stdin import StdinAdapter

processor = missive.Processor()


def is_greeting(message: missive.Message):
    return message.data in [b"hello", b"goodbye"]


@processor.handle_for([is_greeting])
def match_greetings(message) -> None:
    print("match_greetings")
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

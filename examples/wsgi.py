import missive
from missive.adapters.wsgi import WSGIAdapter

processor = missive.Processor[missive.GenericMessage]()


@processor.handle_for([])
def print_everything_out(message, ctx) -> None:
    print(message)
    ctx.ack(message)


adapted = WSGIAdapter(missive.JSONMessage, processor)


if __name__ == "__main__":
    adapted.run()

import missive
from missive.messages import GenericMessage
from missive.adapters.wsgi import WSGIAdapter

processor = missive.Processor[GenericMessage]()


@processor.handle_for([])
def print_everything_out(message) -> None:
    print(message)


adapted = WSGIAdapter(processor)


if __name__ == "__main__":
    adapted.run()

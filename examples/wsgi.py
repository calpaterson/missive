import missive
from missive.adapters.wsgi import WSGIAdapter

processor = missive.Processor()


@processor.handle_for([])
def print_everything_out(message) -> None:
    print(message)


adapted = WSGIAdapter(processor)


if __name__ == "__main__":
    adapted.run()

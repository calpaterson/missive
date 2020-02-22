import missive

processor = missive.Processor()


@processor.handle_for((),)
def print_everything_out(message) -> None:
    print(message)


adapted = missive.StdinAdapter(processor)


if __name__ == "__main__":
    adapted.run()

# Missive

Missive is a framework for writing message (/event) handlers in Python.  It's
best explained with some sample code:

```python
import missive

processor = missive.Processor()

@processor.handler([])
def hello_world(message: Message) -> None:
    print("Hello, World!")
    message.ack()

if __name__ == "__main__":
    processor.run(adapter=missive.adapters.StdinAdapter())
```

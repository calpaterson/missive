# Missive

Missive is a framework for writing message (/event) handlers in Python.

It's best explained with some sample code:

```python
import missive

processor = missive.Processor()

@processor.handle_for((),)
def hello_world(message: Message) -> None:
    print("Hello, World!")
    message.ack()

adapted_processor = missive.adapters.StdinAdapter(processor)

if __name__ == "__main__":
    adapted_processor.run()
```

## Goals, non-goals and planned

Goals:

1. Route messages to the right handlers

    Allow for flask-style decorator based routing configuration

2. Pluggable message transports via adapters

    Support for different message transports (RabbitMQ, Redis, SQS, etc) is
    pluggable and the specific details of the transport are kept out of the
    message handlers.

3. But provide escape hatches when necessary

    However, many message transports provide unique features

4. A test client to allow for testing without running the message transport

    Some message transports (in particular, proprietary ones) cannot be run
    locally.  Even where this is possible it can slow down testing so a test
    client is provided to allow for testing of many cases without a locally
    running message transport.

5. Facility for "dead letter queues" (DLQs) where problem messages can be
   stored for later manual review

   A very common requirement is that "problem" messages (unreadable,
   ambigious, unknown, etc) can be filed away for later manual inspection and
   replay.  DLQs will be pluggable

Non-goals:

1. Message publication

    Publication of messages is different enough from handling that it should be
    in a different library - just as in the web world, requests and flask are
    different libraries too.

2. Message libraries

    Many organisations maintain message "libraries" which contain schemas.
    These are different enough everywhere that they need to be handled by
    custom code.

3. Message validation (beyond that needed for routing)

    Message validation is also a big topic on which missive takes no opinion -
    except that if you are routing based on the internal structure of messages
    that structure needs to be present in the message - otherwise it will be
    sent to the DLQ.

Planned:

1. Metrics

    Somehow

2. Respect for message confidentiality

    Logging message contents is very useful for debugging problems.  However
    some messages contain confidential data.  At some point, missive will
    respect the confidentiality of messages and not log them out.

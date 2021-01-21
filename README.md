# Missive

Missive is a framework for writing message (/event) handlers in Python.

**Please beware that Missive does not (yet) maintain a stable API and is not ready for production use.**

It's best explained with some sample code:

```python
import missive

proc = missive.Processor()

@proc.handle_for(lambda message: True)  # match all messages
def hello_world(message: missive.Message, context: missive.HandlingContext) -> None:
    """Print 'Hello, World!' to stdin for each message"""
    print("Hello, World!")
    context.ack()  # acknowledge the message (a bit redundant for stdin)

adapted_proc = missive.adapters.StdinAdapter(proc)

if __name__ == "__main__":
    adapted_proc.run()
```

**Please note this is all alpha level code**

## Goals, non-goals and planned

Goals:

1. Route messages to the right handlers (**DONE**)

    Allow for flask-style decorator based routing configuration

2. Pluggable message transports via adapters (**DONE**)

    Support for different message transports (RabbitMQ, Redis, SQS, etc) is
    pluggable and the specific details of the transport are kept out of the
    message handlers.

3. But provide escape hatches when necessary (**MISSING**)

    However, many message transports provide unique features and they'll need
    to be accessed - probably on the adapter somewhere.

4. A test client to allow for testing without running the message transport (**DONE**)

    Some message transports (in particular, proprietary ones) cannot be run
    locally.  Even where this is possible it can slow down testing so a test
    client is provided to allow for testing of many cases without a locally
    running message transport.

5. Facility for "dead letter queues" (DLQs) where problem messages can be
   stored for later manual review (**PROOF-OF-CONCEPT**)

    A very common requirement is that "problem" messages (unreadable,
    ambigious, unknown, etc) can be filed away for later manual inspection and
    replay.  DLQs will be pluggable

6. A method for retrying transient failures (**NO LONGER PLANNED**)

    DLQs often get filled with transient failures that need periodic retry.
    Some of of mechanism is needed for periodic retry.  Generic "middleware"
    approaches to be avoided if possible

7. A rich library of matchers (**NO LONGER PLANNED**)

    Matchers can be callables but it would be nice to have better building
    blocks in the form of proper class instances (that also have `__call__`
    defined).


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

    Somehow!

2. Respect for message confidentiality

    Logging message contents is very useful for debugging problems.  However
    some messages contain confidential data.  At some point, missive will
    respect the confidentiality of messages and not log them out.

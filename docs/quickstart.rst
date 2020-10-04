.. _quickstart:

Quickstart
==========

Get started quickly with this guide, covering all the main features of Missive.

A simple example
----------------

.. code-block:: python

    import missive

    from missive.adapters.stdin import StdinAdapter

    processor = missive.Processor()

    @processor.handle_for(lambda m: m.raw_data == b"Hello")
    def greet(message, ctx):
        print("Hello whoever you are")
        ctx.ack(message)

    stdin_processor = StdinAdapter(missive.RawMessage, processor)

    if __name__ == "__main__":
        stdin_processor.run()

The above code:

1. Creates a new processor called "processor"
2. Creates a new handler for b"Hello" messages
3. Adapts the processor for stdin
4. (If the file is being run directly), runs the processor

Save this as `hello_processor.py` and then run it:

.. code-block:: text

    python3 hello_processor.py

Routing and matchers
--------------------

Missive routes incoming messages to specific handlers based on the matchers
provided.  In the example above the matcher is a lambda function but matchers
can be any python Callable - for example `def` functions or classes that
implement the `__call__` method.  Here's a sample class:

.. code-block:: python

    class HasLabelMatcher:
        def __init__(self, label):
            self.label = label

        def __call__(self, json_message):
              return json_message.get_json().get("label") == label

The above matcher class will match any messages with the label matching what it
was constructed with.  Here's how you might use it:

.. code-block:: python

    processor = missive.Processor()

    @processor.handle_for(HasLabelMatcher("sign-in"))
    def record_sign_ins(message, ctx):
        ...

    @processor.handle_for(...)
    def another_matcher(message, ctx):
        ...

The above processor would route messages with the label `"sign-in"` to the
`record_sign_ins` handler.

Matchers help ensure that messages of certain types are sent directly to the
relevent code for dealing with them.

Message formats
---------------

You will notice that the above example had a message with a `get_json` method.
That was a `JSONMessage` instead of a `RawMessage`.  Processors can be
specialised on specific message types.  Some popular message types are provided
and custom message types can be written easily by subclassing `Message`.

If you are using Python's typechecking facilities you can enforce message types
by applying a type to your processor:

.. code-block:: python

    # All handlers for this message will be typechecked against JSONMessage
    json_processor: missive.Processor[missive.JSONMessage] = missive.Processor()

Pluggable adapters
------------------

The initial example used a "stdin" adapter but adapters are pluggable and not
(usually) tied up with the message format that you are using.

Instead of running a message processor using unix's stdin and stdout you might
want to use Redis's PubSub facility:

.. code-block:: python

    from missive.adapters.redis import RedisPubSubAdapter
    redis_pubsub_processor = RedisPubSubAdapter(
        missive.RawMessage,
        processor)

    redis_pubsub_processor.run()

As you can see, changing the transport mechanism for messages is just a matter
of what adapter is used.  Just as with message formats, some adapters are
provided but custom adapters can be (somewhat) easily written by subclassing
the abstract `Adapter` class.

.. note:: Using HTTP

    One important adapter is the WSGIAdapter, which allows message processors
    to be run as web applications (via a WSGI server such as gunicorn or
    uwsgi).  This can be a handy way to provide a web API for message senders
    than for whatever reason can't or don't want to connect to your message
    bus.


Testing
-------

One very important feature is the ability to run tests without sending messages
over a real instance of your chosen message bus.  Missive includes a test
client that allows for this:

.. code-block:: python

    import json

    test_client = json_processor.test_client()
    message = missive.JSONMessage(json.dumps({"name": "Cal"}).encode("utf-8"))

    test_client.send(message)

    assert message in test_client.acked
    assert ... # anything else

There are a number of advantages to making use of a special test client that
cuts out the real message bus:

1. It's easier to assert that messages are acked/nacked/etc
2. It's much faster than using a real message bus (and tests can be run in parallel)
3. It removes the need for test code to navigate the background threading
   patterns that are common in the real adapters.

Dead letter queues (DLQs)
-------------------------

One of the first questions that comes up in message processing systems is:

    What should I do when an error occurs during message processing?

Unlike when writing request-response model applications (like web APIs), where
errors can be reported directly to the client, in publish-subscribe models the
emitter of the message often is not able (or interested) in receiving an error
from your processor.

What to do then?  The answer is to have a special storage location for messages
that cause errors in your system so that you can save them for manual
inspection or debugging.  It might be that some messages are improperly
formatted or that your application has bugs.

.. note:: The "non-ack anti-pattern"

    One important anti-pattern to avoid in message processors is failing to ack
    unprocessable messages.  This leaves them on the bus (often causing them to
    be reprocessed over and over) eventually clogging up the bus and causing
    further problems.

This special place is called a "dead letter queue".  Missive provides a way to
register a location in which to put unprocessable messages to get them out of
the message bus and somewhere else where they can be kept until they can be
debugged.

.. code:: python

    from missive.dlq.sqlite import SQLiteDLQ

    # Problem messages will be written to this sqlite database
    json_processor.set_dlq(SQLiteDLQ("/var/dlq.db"))

.. warning:: "DLQs" are poorly named

    Despite the fact that DLQs are "dead letter *queues*", message queues are
    usually a bad places for a DLQ.  Message queues are designed for fast
    moving, in-and-out items.  Dead letter queues need to be ready to deal with
    slower moving items that are occasionally very numerous - in the case where
    someone puts a lot of bad messages onto a shared bus.

    A database is usually the right place.

What's not included
-------------------

Message publication
^^^^^^^^^^^^^^^^^^^

Missive is focused on message *processing* and not message publication.  There
are lots of different ways to emit messages and Missive does not try to be an
all-encompassing mechanism for being systems that emit and recieve messages.

This would be of limited use anyway - messages are a common means of
inter-system communication.  The publisher of messages may well be a Java or
C++ application.

Message libraries
^^^^^^^^^^^^^^^^^

Likewise Missive does not try to manage message libraries or schemas.  There
are many many different ways to communicate schemas in-band or out-of-band and
Missive aims to be able to handle all of them but does not seek control of the
message schema.

Message validation
^^^^^^^^^^^^^^^^^^

Missive is not a validation library and if you want to apply validation rules
to messages you will need to do that yourself.

Key features
============

Missive is not in general an "opinionated" framework but it does have certain
ideas as key principles.

.. warning::
   Missive is in an early stage and not all of the promises here are yet
   implemented.

Easy routing
------------

Routing messages to their appropriate handlers is repetitive, error prone
code.  Missive provides an easy interface for using message "matchers" to
indicate which handlers are to be applied to which messages.

The interface is dead simple: any callable taking a message as an argument and
returning a boolean is a valid matcher.

Pluggable adapters
------------------

Missive is designed to allow your core message handling code to be agnostic
about which message transport system has delivered the message.  This is done
by providing pluggable adapters into which :class:`missive.Processor` objects
are inserted.

Using pluggable adapters has a number of practical advantages.

Pluggable adapters also allows you to easily change your mind about which
message transport you will use.  If late in the project you learn that a key
message publisher will not be allowed to connect to your message bus you will
be able to offer them webhook-style access via the
:class:`missive.adapters.wsgi.WSGIAdapter`.  If your organisation switches from
Redis to Kafka (or vice versa) you will be able to switch out one adapter for
another and run the same code.

An easy way to write fast tests
-------------------------------

Writing automated tests is essential to producing good quality software.  Tests
that interface with third-party systems such as your message bus are essential.

That said, it is not necessary that every test write to and from your message
bus.  It's helpful to write the majority of your unit tests assuming that your
message bus will work as expected and spare your time suite the time and
complexity of putting every test message over the real bus.

Worse yet: some message buses are too proprietary (or licensing too expensive)
for developers to be able to run them locally.  Having pluggable adapters
allows processors to be tested with one adapter (usually
:class:`missive.TestAdapter`) and finally deployed onto another.  It used to be
that this was only the case in the financial sector but with the rise of cloud
computing many message transports cannot be run locally at all.

Dead letter queues
------------------

One of the biggest stumbling blocks in writing message processors is in
handling messages that, for whatever reason, cannot be processed.

Counter-intuitively, despite the fact that this messages cannot be processed
correctly they must regardless be acked to prevent them from being repeatedly
redelivered - lowering throughput and creating congestion.

Unprocessable messages need to be stored somewhere for manual inspection and
debugging.  Missive provides a simple interface for doing so and comes,
"batteries included" with a few well designed dead letter queue options.

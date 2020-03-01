Adapters
========

Adapters transform :class:`missive.missive.Processor` instances into working
message processors for the message transport which they implement.

The adapter system used in Missive allows any processor to be ported easily
between different message transports.

.. note::

   Porting between adapters assumes that no transport-specific features are
   being used!  For example, if message leases are being extended via a
   transport-specific system then that handler is obviously no longer portable
   between transports.

   Missive provides tools to help you avoid transport-specific code but "escape
   hatches" are always provided.

Built-in adapters
-----------------

Missive comes with adapters for some message transports.  Over time it is hoped that
wider support can be added.  If support for a transport you want is not present
it should not be too hard to add, see :ref:`custom_adapters`.

Stdin
^^^^^

One useful source of messages (particularly for testing or local reply) is
traditional unix pipes and files.

.. autoclass:: missive.adapters.stdin.StdinAdapter
           :noindex:
           :members:

WSGI
^^^^

WSGI is the standard Python way of serving over HTTP.  Many different "WSGI
servers" exist which will efficiently serve a "WSGI application" for example
gunicorn and uwsgi.

.. autoclass:: missive.adapters.wsgi.WSGIAdapter
           :noindex:
           :members:

The WSGI adapter is useful for implementing "webhooks" (special endpoints that
other services will call when events happen).

It also allows you to make your processor available over HTTP to allow access
to it for users who for whatever reason aren't able to use a "proper" message
transport.

It is also often the easiest thing to get deployed anywhere - running a new web
service is typically easy in most organisations but running a new message bus
is not.

.. note::

    HTTP is comparatively slow - offering services over HTTP is convenient but
    there is a much higher associated overhead compared to using a true message
    transport.

Redis
^^^^^

Missive has built-in support for `Redis's Pub/Sub
<https://redis.io/topics/pubsub>`_ functionality.

.. autoclass:: missive.adapters.redis.RedisPubSubAdapter
               :noindex:
               :members:

.. _custom_adapters:

Writing custom adapters
-----------------------

Writing a custom adapter is as simple as subclassing
:class:`missive.missive.Adapter` and implementing an `ack` and a `nack` method.

.. autoclass:: missive.Adapter
               :noindex:
               :members:

The way that the adapter is to be run is completely undefined.  Many adapters
define a `run` method that makes the necessary network connections but this can
vary widely and is not mandated.

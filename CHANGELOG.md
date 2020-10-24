# Changelog

This is the changelog for missive.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/).

Please note that prior to version 1.0 Missive will make (considerable) backward
incompatible changes as the API is fleshed out.

## Unreleased

- Add a system of hooks and state
  - There are hooks for when processing starts, stops and when handling of a
    given message starts and stops
  - The specific aim here is to allow for SQL connections and connection pools
  - This changes a number of different call signatures across the codebase
- Ack and nack messages specifically in the RabbitMQAdapter
  - This fixes a bug where acks and nacks were getting mixed up due to async
    magic happening inside pyamp (there can be multiple messages in flight)


## [0.6.0] - 2020-10-05

- Change `Processor.handle_for` to take a single matcher instead of a sequence
- Using the same matcher multiple times will now raise an exception on import
- `GenericMessage` is now called `RawMessage`
- If a handler raises an exception and there is a DLQ configured, that message
  will be put on the DLQ and the message will be acked
- Make the `drain_timeout` on `RabbitMQAdapter` configurable and reduce the default
  from 5 to 1
- `RabbitMQAdapter` can now take either a url or a conn, in order to share a
  connection (it will create it's own channel)
- `RabbitMQAdapter` now implements nacks
- `RabbitMQAdapter` now has a (configurable) default prefetch of 50 messages
- `RabbitMQAdapter` will now ask for messages in it's prefetch queue to be
  requeued upon shutdown


## [0.5.2] - 2020-09-30

- RabbitMQAdapter now has an optional url parameter
- RabbitMQAdapter now supports consuming multiple queues
- Lower many log levels in RabbitMQAdapter from INFO to DEBUG
- Prevent pytest from collecting TestAdapter
- Loosen dependencies

# Changelog

This is the changelog for missive.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

- Change `Processor.handle_for` to take a single matcher instead of a sequence
- Make the `drain_timeout` on the RabbitMQ configurable and reduce the default
  from 5 to 1
- Using the same matcher multiple times will now raise an exception on import
- `GenericMessage` is now called `RawMessage`
- `RabbitMQAdapter` can now take either a url or a conn, in order to share a
  connection (it will create it's own channel)
- `RabbitMQAdapter` now implements nacks

## [0.5.2] - 2020-09-30

- RabbitMQAdapter now has an optional url parameter
- RabbitMQAdapter now supports consuming multiple queues
- Lower many log levels in RabbitMQAdapter from INFO to DEBUG
- Prevent pytest from collecting TestAdapter
- Loosen dependencies

# Changelog

This is the changelog for missive..

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/).

## Unreleased

- Make the `drain_timeout` on the RabbitMQ configurable and reduce the default
  from 5 to 1

## [0.5.2] - 2020-09-30

- RabbitMQAdapter now has an optional url parameter
- RabbitMQAdapter now supports consuming multiple queues
- Lower many log levels in RabbitMQAdapter from INFO to DEBUG
- Prevent pytest from collecting TestAdapter
- Loosen dependencies

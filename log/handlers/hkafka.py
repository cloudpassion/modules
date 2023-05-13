# -*- coding: utf-8 -*-
# https://stackoverflow.com/a/50489652
"""Module to provide kafka handlers for internal logging facility."""

import logging
import asyncio

try:
    import ujson as json
except ImportError:
    import json

try:
    from kafka import KafkaProducer
except:
    pass


class KafkaHandler(logging.Handler):
    """Class to instantiate the kafka logging facility."""

    def __init__(self, hostlist,
                 topic='corp_it_testing', user=None, script=None, level='normal',
                 tls=None):
        """Initialize an instance of the kafka handler."""
        logging.Handler.__init__(self)
        self.producer = KafkaProducer(
            bootstrap_servers=hostlist,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            linger_ms=10)
        self.topic = topic
        if user:
            self.user = user
        else:
            self.user = topic

        if script:
            self.script = script
        else:
            self.script = topic

        self.log_level = level

    def emit(self, record):
        """Emit the provided record to the kafka_client producer."""
        # drop kafka logging to avoid infinite recursion
        if 'kafka.' in record.name:
            return

        try:
            # apply the logger formatter
            msg = self.format(record)
            self.producer.send(self.topic, {
                'message': msg,
                'source': 'python_handler',
                'log_level': self.log_level,
                'user': self.user,
                'script': self.script,
                'funcname': record.funcName,
                'pathname': record.pathname,
                'lineno': record.lineno,
            })
            self.flush(timeout=1.0)
        except Exception:
            logging.Handler.handleError(self, record)

    def flush(self, timeout=None):
        """Flush the objects."""
        self.producer.flush(timeout=timeout)

    def close(self):
        """Close the producer and clean up."""
        self.acquire()
        try:
            if self.producer:
                self.producer.close()

            logging.Handler.close(self)
        finally:
            self.release()


def init_kafka_handler(address='127.0.0.1:9980',
                       topic='test_kafka_g076nLnHqn8', user=None, script=None,
                       level='normal'):
    """Run the actual connections."""

    handler = KafkaHandler([address], topic, user, script, level,
                           tls=True if 'https' in address else None)

    return handler

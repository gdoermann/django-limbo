import logging
from limbo.logs import TimeStampedRotatingFileHandler

__author__ = 'gdoermann'

class AmqpRotatingHandler(TimeStampedRotatingFileHandler):
    pass

class AmqpLogger(logging.Logger):
    """
    This logger allows you to override anything you want in the logger dict.
    This allows you to log messages from other machines and show the log
    messages as they would appear on that machine, not from the emitter
    on the amqp handler.
    """
    def makeRecord(self, name, level, fn, lno, msg, args, exc_info, func=None, extra=None):
        rv = logging.LogRecord(name, level, fn, lno, msg, args, exc_info, func)
        if extra is not None:
            for key in extra:
                rv.__dict__[key] = extra[key]
        return rv


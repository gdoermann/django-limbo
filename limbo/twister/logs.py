import logging
import logging.handlers
import os
from twisted.internet.defer import CancelledError, inlineCallbacks
from twisted.internet.threads import deferToThread
from twisted.internet import reactor
from limbo.logs import TimeStampedRotatingFileHandler, LoggingMixin
from limbo.twister.inline import inline_defer_to_thread

DATEFORMAT = '%d/%b/%Y %H:%M:%S'
LINESEP = os.linesep
INDENT = ' ' * 10

# standard Python logging levels
LEVELS = [logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL]

class TwistedTimeStampedRotatingFileHandler(TimeStampedRotatingFileHandler):
    def emit(self, record):
        if reactor and reactor.running:
            deferToThread(logging.handlers.RotatingFileHandler.emit, self, record)
        else:
            logging.handlers.RotatingFileHandler.emit(self, record)

class TwistedStreamHandler(logging.StreamHandler):
    def emit(self, record):
        if reactor and reactor.running:
            deferToThread(logging.StreamHandler.emit, self, record)
        else:
            logging.StreamHandler.emit(self, record)

class TwistedNTEventLogHandler(logging.handlers.NTEventLogHandler):
    """
    Note: This handler could cause system latency at startup only. These
    log handlers are not Twisted aware at the instantiation point, but
    the emit methods are.
    """
    def emit(self, record):
        if reactor and reactor.running:
            deferToThread(logging.handlers.NTEventLogHandler.emit, self, record)
        else:
            logging.handlers.NTEventLogHandler.emit(self, record)

class TwistedSysLogHandler(logging.handlers.SysLogHandler):
    """
    Note: This handler could cause system latency at startup only. These
    log handlers are not Twisted aware at the instantiation point, but
    the emit methods are.
    """
    def emit(self, record):
        if reactor and reactor.running:
            deferToThread(logging.handlers.SysLogHandler.emit, self, record)
        else:
            logging.handlers.SysLogHandler.emit(self, record)

class TwistedLoggingMixin(LoggingMixin):
    @inlineCallbacks
    def _log(self, msg, log_level=None, *args, **kwargs):
        inline_defer_to_thread(super(TwistedLoggingMixin, self)._log, msg, log_level, *args, **kwargs)

    def log_deferred_failure(self, err, *args, **kwargs):
        if err.check(CancelledError):
            return
        else:
            self.log_error(err.getTraceback())

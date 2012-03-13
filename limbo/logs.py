import logging
import logging.handlers
import os
import re
import sys
import datetime
import traceback
from django.utils.datastructures import SortedDict

DATEFORMAT = '%d/%b/%Y %H:%M:%S'
LINESEP = os.linesep
INDENT = ' ' * 10

# standard Python logging levels
LEVELS = [logging.DEBUG, logging.INFO, logging.WARNING,
            logging.ERROR, logging.CRITICAL]

class TimeStampedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=1024*1024*10, backupCount=None, encoding=None, delay=0,
                 date_format='%Y.%m.%d.%H%M%S%f'):
        self.last_rollover = datetime.datetime.now()
        self.date_format = date_format
        logging.handlers.RotatingFileHandler.__init__(self, filename, mode, maxBytes, backupCount, encoding, delay)

    @property
    def rollover_filename(self):
        return '%s.%s' %(self.baseFilename, datetime.datetime.now().strftime(self.date_format))

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        if self.backupCount is not None:
            return super(TimeStampedRotatingFileHandler, self).doRollover()

        if self.stream:
            self.flush()
            self.stream.close()
            self.stream = None
            # We don't have to worry about overlap as the name is based on the datetime.
        # You should include up to milliseconds to make sure there is no naming conflicts.

        if os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, self.rollover_filename)
        self.last_rollover = datetime.datetime.now()
        self.stream = self._open()

class StdWrapper(object):
    is_err = False
    logger = logging.getLogger('std')
    def __init__(self, stream=None):
        self.stream = stream

    def write(self, s):
        self.emit(s, self.is_err)
        if self.stream:
            self.stream.write(s)

    def emit(self, msg, is_stderr = False):
        msg = msg.rstrip('\n').lstrip('\n')
        p_level = r'^(\s+)?\[(?P<LEVEL>\w+)\](\s+)?(?P<MSG>.*)$'
        m = re.match(p_level, msg)
        if m:
            msg = m.group('MSG')
            if m.group('LEVEL') in ('WARNING'):
                self.logger.warning(msg)
                return
            elif m.group('LEVEL') in ('ERROR'):
                self.logger.error(msg)
                return
        msg = msg
        if is_stderr:
            self.logger.error(msg)
        else:
            self.logger.info(msg)

class StdOutWrapper(StdWrapper):
    """
        Call wrapper for stdout
    """
    logger = logging.getLogger('std.stdout')


class StdErrWrapper(StdWrapper):
    """
        Call wrapper for stderr
    """
    logging.getLogger('std.stderr')
    is_err = True

def std_to_log(stdout_wrapper = StdOutWrapper, stderr_wrapper = StdErrWrapper):
    if stdout_wrapper and not isinstance(sys.stdout, StdWrapper):
        sys.stdout = stdout_wrapper(sys.stdout)
    if stderr_wrapper and not isinstance(sys.stderr, StdWrapper):
        sys.stderr = stderr_wrapper(sys.stderr)


class LoggingMixin(object):
    default_logger = None
    default_log_level = logging.DEBUG

    def __init__(self):
        super(LoggingMixin, self).__init__()
        self._check_default_logger()

    def _check_default_logger(self):
        if not self.default_logger:
            self.default_logger = logging.getLogger('%s.%s' %(self.__class__.__module__, self.__class__.__name__))
            if self.default_log_level:
                self.default_logger.setLevel(self.default_log_level)

    def log_header_dict(self, *args, **kwargs):
        """
        To be implemented in child classes.  This will define what goes in the log header.
        This can be different for each log record dependant on the state of the object.
        """
        return SortedDict()

    def log_header(self, *args, **kwargs):
        lhd = SortedDict([(k, v) for k, v in self.log_header_dict(*args, **kwargs).items() if v is not None])
        if not lhd:
            return ''
        header = '|'.join('%s:%s' % item for item in lhd.items())
        return '{%s} ' %(header.strip())

    def log(self, msg, log_level=None, *args, **kwargs):
        if log_level is None:
            log_level = self.default_log_level
            # Just uses default log
        self._log(msg, log_level, *args, **kwargs)

    def _log(self, msg, log_level=logging.DEBUG, *args, **kwargs):
        try:
            self._check_default_logger()
            header = self.log_header(*args, **kwargs)
            self.default_logger.log(log_level, header + str(msg))
        except Exception:
            logger = logging.getLogger(__name__)
            logger.error(traceback.format_exc(50))

    def log_debug(self, msg, *args, **kwargs):
        self.log(msg, logging.DEBUG, *args, **kwargs)

    def log_info(self, msg, *args, **kwargs):
        self.log(msg, logging.INFO, *args, **kwargs)

    def log_warning(self, msg, *args, **kwargs):
        self.log(msg, logging.WARNING, *args, **kwargs)

    def log_error(self, msg, *args, **kwargs):
        self.log(msg, logging.ERROR, *args, **kwargs)

    def log_exception(self, msg, *args, **kwargs):
        self.log(msg, logging.ERROR, *args, **kwargs)

    def log_critical(self, msg, *args, **kwargs):
        self.log(msg, logging.ERROR, *args, **kwargs)

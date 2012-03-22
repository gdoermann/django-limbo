from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks, returnValue

__author__ = 'gdoermann'


class DeferredLock(object):
    """
    This uses deferred to wait until something has finished.
    """
    def __init__(self):
        self.deferred = None

    @property
    def locked(self):
        return bool(self.deferred)

    def lock(self):
        if self.locked:
            return # Already locked
        self.deferred = defer.Deferred()

    def unlock(self, *args, **kwargs):
        if self.deferred:
            d = self.deferred
            self.deferred = None
            if not d.called:
                if not args and not kwargs:
                    args = [None]
                d.callback(*args, **kwargs)

    @inlineCallbacks
    def wait(self):
        yield self.deferred
        returnValue(None)
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.threads import deferToThread

@inlineCallbacks
def inline_defer_to_thread(method, *args, **kwargs):
    """
    This will call any non-twisted method on a thread and return the value
    in an inlineCallbacks way.
    """
    d = deferToThread(method, *args, **kwargs)
    val = yield d
    returnValue(val)
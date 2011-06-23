import datetime
from django.db.transaction import TransactionManagementError
import logging
from south.db import db
from django.core.cache import cache
from decimal import Decimal
import gc

log = logging.getLogger(__file__)

def move_fields(from_model, to_model, **fields):
    """ Map fields from one model to another model in a
    south data migration.
    @param from_model:  The model you are taking the attributes from
    @param to_model:    The model you are setting the attributes on
    @param fields:      The from_attr -> to_attr map of attributes on the from_model to the to_model
    """
    for from_attr, to_attr in fields.items():
        setattr(to_model, to_attr, getattr(from_model, from_attr))
    return to_model

def copy_fields(from_model, to_model, *fields):
    """ Same as move_fields, but it takes a list of attributes to move over.
        All attributes must exist on both models
    """
    map = dict((f, f) for f in fields)
    return move_fields(from_model, to_model, **map)

class UpdateTracker:
    def __init__(self, total, commit_number = None, name = ''):
        self.total = total
        self.count = 0
        self.commit_number = commit_number
        self.committed = None
        self.start_time = None
        self.name = name
        self.rate = None
        self.remaining = None
        if self.commit_number:
            db.start_transaction()
        self.plog(0)

    def ping(self, count = 1):
        if not self.count:
            self.start_time = datetime.datetime.now()
            self.log()
        self.count += count

    def calc_rate(self):
        if not self.start_time:
            return
        tdiff = datetime.datetime.now() - self.start_time
        seconds = tdiff.days * 24 * 60 * 60 + tdiff.seconds
        if not seconds:
            return
        rate_s = Decimal(str(self.count)) / Decimal(str(seconds))
        self.rate = '%d / second' %rate_s
        self.remaining = datetime.timedelta(seconds = int((Decimal(str(self.total)) - Decimal(str(self.count)))/ rate_s))

    def log(self):
        self.calc_rate()
        s = "\r%i/%i %s finished" % (self.count, self.total, self.name)
        if self.committed is not None:
            s +=" | %i committed" % self.committed
        if self.rate:
            s += ' | %s | %s remaining' %(self.rate, self.remaining)
        if self.total == self.count:
            print s
        else:
            print s,

    def plog(self, count = 1):
        self.ping(count)
        if self.commit_number:
            self._check_commit()
        if not self.count%50 or self.count == self.total:
            self.log()

    def _check_commit(self):
        if not self.count%self.commit_number or self.count==self.total:
            self.commit()

    def commit(self):
        try:
            db.commit_transaction()
            self.committed = self.count
            cache.clear()
            gc.collect()
            gc.collect()
            db.start_transaction()
        except TransactionManagementError:
            pass

def queryset_generator(q, step = 10000):
    start = 0
    n = step
    max = q.count()
    while n <= max:
        yield q._clone()[start:n]
        start = n
        if n == max:
            break
        n += step
        if n > max:
            n = max

class LargeQuerysetUpdater:
    """ Takes very large querysets and updates them
    conserving memory and resources """
    def __init__(self, q, commit_after=10000):
        self.q = q
        if q.count():
            first = q[0]
            name = first.__class__.__name__
        else:
            name = ''
        self.tracker = UpdateTracker(q.count(), None, name= name)
        self.commit_after = commit_after

    def update(self, method):
        for q in queryset_generator(self.q, self.commit_after):
            for obj in q.iterator():
                method(obj)
                self.tracker.plog()
            self.tracker.commit()
        self.tracker.commit()

    def commit(self):
        self.tracker.commit()

class LargeQuerysetDeleter:
    def __init__(self, q, name = None, chunk = 100000):
        self.q = q
        if name is None:
            try:
                name = q[0].__class__.__name__
            except IndexError:
                pass
        self.tracker = UpdateTracker(q.count(), chunk, name= name)
        self.chunk = chunk

    def delete(self):
        q = self.q.order_by('pk')
        chunk = self.chunk
        self.tracker.log()
        while q.count() > chunk:
            q2 = q.filter(pk__lt=q[chunk].pk)
            q2.delete()
            self.tracker.plog(chunk)
            q = q._clone() # Reset queryset cache
        c = q.count()
        q.delete()
        self.tracker.plog(c)
import datetime
from django.utils.datastructures import SortedDict

__author__ = 'gdoermann'

class RunningAverage(object):
    def __init__(self, max=datetime.timedelta(minutes=30)):
        """
        @param max: Max duration after which data will be dropped
        """
        super(RunningAverage, self).__init__()
        self._items = SortedDict()
        self.max = max

    def append(self, item, dtime = None):
        if not dtime:
            dtime = self.now()
        self._items[dtime] = item

    def remove(self, *items):
        for key in items:
            if self._items.has_key(key):
                del self._items[key]

    def sum(self, items):
        return sum([float(item) for item in items])

    def average(self, items):
        if not items:
            return None
        return self.sum(items)/float(len(items))

    def time_average(self, delta):
        now = self.now()
        values = []
        for key, value in self._items.items():
            diff = now - key
            if diff > self.max:
                self.remove(key)
            elif diff <= delta:
                values.append(value)
        return self.average(values)

    def rate(self, delta):
        if not self._items:
            return None
        now = self.now()
        values = []
        last_dtime = None
        last_value = None
        for key, value in self._items.items():
            diff = now - key
            if diff > self.max:
                self.remove(key)
            elif diff <= delta:
                if not last_dtime:
                    last_dtime = key
                    last_value = value
                    continue
                rate = key - last_dtime
                seconds = rate.seconds + rate.days*86400
                if not seconds:
                    last_value += value
                    continue
                values.append(float(value - last_value) / float(seconds))
                last_dtime = key
                last_value = value
        return self.average(values)

    def now(self):
        """
        Ability to alter resolution of time
        """
        return datetime.datetime.now()
    
    def averages(self, *deltas):
        if not deltas:
            deltas = [datetime.timedelta(minutes=1)]
        values = []
        for delta in deltas:
            values.append(self.time_average(delta))
        return tuple(values)

    def rates(self, *deltas):
        if not deltas:
            deltas = [datetime.timedelta(minutes=1)]
        values = []
        for delta in deltas:
            values.append(self.rate(delta))
        return tuple(values)

    def __call__(self, *deltas):
        return self.averages(*deltas)

class CountRunningAverage(RunningAverage):

    def ping(self, count=1):
        now = self.now()
        if self._items.has_key(now):
            self._items[now] += count
        else:
            self._items[now] = count


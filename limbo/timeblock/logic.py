from copy import copy
from decimal import Decimal
from limbo.timeblock import exceptions
from limbo.timeblock.util import *
from limbo.timeblock import calcs

class TimeBlock(object):
    def __init__(self, start, end):
        start, end = calcs.get_start_end(start, end)
        self.start = start
        self.end = end
        if end < start:
            self.end = start
            self.start = end
        assert(self.start <= self.end)

    def before(self, other):
        return self.__lt__(other)

    def after(self, other):
        return self.__gt__(other)

    def overlaps(self, other):
        if self.before(other) or self.after(other):
            return False
        return True

    def get_start(self):
        return getattr(self, '_start', None)

    def set_start(self, start):
        setattr(self, '_start', start)
        setattr(self, '_cstart', ComparibleDateTime(start))
    start = property(get_start, set_start)

    def get_cmp_start(self):
        return getattr(self, '_cstart', None)
    cmp_start = property(get_cmp_start)

    def get_end(self):
        return getattr(self, '_end', None)
    def set_end(self, end):
        setattr(self, '_end', end)
        setattr(self, '_cend', ComparibleDateTime(end))
    end = property(get_end, set_end)

    def get_cmp_end(self):
        return getattr(self, '_cend', None)
    cmp_end = property(get_cmp_end)


    def _force_overlap(self, other):
        if not self.overlaps(other):
            raise exceptions.TimeblockOverlapError('Time blocks do not overlap')

    def fully_overlaps(self, other):
        """ See if this block fully overlaps the other """
        return self.start <= other.start and self.end >= other.end  and not self==other

    def _force_full_overlap(self, other):
        if not (self.fully_overlaps(other) or other.fully_overlaps(self)):
            raise exceptions.TimeblockFullOverlapError('One time block must fully overlap the other')

    def split(self, other):
        if self == other:
            return tuple()
        self._force_full_overlap(other)
        if self.fully_overlaps(other):
            gblock = self
            lblock = other
        else:
            lblock = self
            gblock = other
        b1 = TimeBlock(gblock.start, lblock.start)
        b2 = TimeBlock(lblock.end, gblock.end)
        if gblock.start == lblock.start:
            return b2,
        elif gblock.end == lblock.end:
            return b1,
        else:
            return b1, b2

    @property
    def duration(self):
        return self.end - self.start

    def subsequent(self, other):
        return other.start == self.end or other.end == self.start

    def __lt__(self, other):
        return self.cmp_end < ComparibleDateTime(other.start)

    def __le__(self, other):
        return self.cmp_end <= ComparibleDateTime(other.start)

    def __gt__(self, other):
        return self.cmp_start > ComparibleDateTime(other.end)

    def __ge__(self, other):
        return self.cmp_start >= ComparibleDateTime(other.end)

    def __eq__(self, other):
        return self.cmp_start == ComparibleDateTime(other.start) and self.cmp_end == ComparibleDateTime(other.end)

    def __add__(self, other):
        """ Returns a single, combined timeblock """
        self._force_overlap(other)
        start = min(other.start, self.start)
        end = max(other.end, self.end)
        return TimeBlock(start, end)

    def __sub__(self, other):
        """ Returns None if they are equal or the other one fully overlaps this one
            Returns a single TimeBlock with the difference otherwise
            If this block fully overlaps the other block it will throw a value error as you must splice the two
        """
        self._force_overlap(other)
        if other.start == self.end: # Tested
            return copy(self)
        elif any([
                         other.start <= self.start and self.end == other.end,
                         other.start == self.start and other.end >= self.end,
                         ]): # Tested
            return None
        elif (
             other.fully_overlaps(self) or self.fully_overlaps(other)
             ) and not (
        other.end == self.end or other.start == self.start
        ): # Tested
            raise exceptions.TimeblockArithmeticError('Cannot subtract. You must split this block')
        elif other <= self: # Tested
            raise exceptions.TimeblockOverlapError('The other time block must be after this time block')
        elif other.end == self.end: # Tested
            return TimeBlock(self.start, other.start)
        elif other.start == self.start: # Tested
            return TimeBlock(other.end, self.end)
        elif other.start < self.start: # Tested
            start = other.end
            end = self.end
            return TimeBlock(start, end)
        elif other.end > self.end: # Tested
            start = self.start
            end = other.start
            return TimeBlock(start, end)
        else:
        # No clue what would slip by...
            raise exceptions.TimeblockError("Unhandled subtraction type: %s - %s" %(self, other))

    def __str__(self):
        return '%s - %s' %(self.start.__str__(), self.end.__str__())

    def __repr__(self):
        return self.__str__()

class UnscheduledBlock(TimeBlock):
    def __init__(self, start, end, user):
        super(UnscheduledBlock, self).__init__(start, end)
        self.user = user

class TimeChoices(dict):
    def __init__(self, timeblocks = list(), increment = 15, space = 15):
        dict.__init__(self)
        self.increment = increment
        self.space = float(space)

        for block in timeblocks:
            self.append(block)

    def append(self, block):
        date = block.start.date()
        vals = self.get(date, None)
        if vals is None:
            vals = []
            self[date] = vals
        ctime = self.round(block.start)
        while ctime + datetime.timedelta(minutes=self.space) <= block.end:
            if ctime not in vals:
                vals.append(ctime)
            ctime += datetime.timedelta(minutes=self.increment)

    def remove(self, block):
    # Does not work if timeblock spans over several days
        date = block.start.date()
        vals = self.get(date, None)
        if not vals:
            return
        ctime = self.round(block.start)
        while ctime + datetime.timedelta(minutes=self.space) <= block.end:
            if ctime in vals:
                vals.remove(ctime)
            ctime += datetime.timedelta(minutes=self.increment)

    def round(self, dtime):
        rounded = int(round(dtime.minute/Decimal(self.increment))*self.increment)
        diff = Decimal(rounded) - Decimal(dtime.minute)
        return dtime + datetime.timedelta(minutes=float(diff))

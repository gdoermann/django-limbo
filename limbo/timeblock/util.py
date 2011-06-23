import calendar
import datetime

def filter_date(queryset, attr = 'date', year = None, month = None, day = None):
    d = {}
    if year:
        d[attr + '__year'] = year
    if month:
        d[attr + '__month'] = month
    if day:
        d[attr + '__day'] = day
    return queryset.filter(**d)

def days_in_month(year = None, month = None):
    """ Calculates the number of days in a month """
    d = datetime.datetime.now()
    year = year or d.year
    month = month or d.month
    return max(max(calendar.monthcalendar(year, month)))

def days_left_in_year(year = None, month = None, day = None):
    """ Calculates the number of days left in a given year """
    d = datetime.datetime.now()
    year = year or d.year
    month = month or d.month
    day = day or d.day

    stamp = datetime.datetime(year, month, day)
    diff = datetime.datetime(year + 1, 1, 1) - stamp
    return diff.days

class DateFilter:
    def __init__(self, year = None, month = None, day = None):
        self.string_year = year
        self.string_month = month
        self.string_day = day
        self.parse()

    def parse(self):
        now = datetime.datetime.now()
        default_date = now

        year = int(self.string_year or default_date.year)
        if self.string_year and not self.string_month and year != now.year:
            default_date = datetime.date(year, 12, 31)

        month = int(self.string_month or default_date.month)

        default_day = now.day
        if year != now.year or month != now.month and not sday:
            if not self.string_month:
                default_day = default_date.day
            else:
                default_day = days_in_month(year, month)

        if self.string_day:
            day = int(self.string_day)
        else:
            day = None

        self.default_date = default_date
        self.year = year
        self.month = month
        self.day = day
        self.default_day = default_day
        self.date = datetime.date(year, month, day or default_day)

    def filter(self, object, attr):
        return filter_date(object, attr, self.year, self.month, self.day)

    @property
    def days_in_month(self):
        return days_in_month(self.year, self.month)

class ComparibleDateTime:
    """ Allows for comparison of date and datetime objects """
    def __init__(self, dtime):
        self.dtime = dtime

    def __str__(self):
        return str(self.dtime)

    def __cmp__(self, other):
        if isinstance(other, ComparibleDateTime):
            other = other.dtime
        if isinstance(other, datetime.datetime) and not isinstance(self.dtime, datetime.datetime):
            if cmp(self.dtime, other.date()) is 0:
                return -1
            else:
                return cmp(self.dtime, other.date())
        elif isinstance(self.dtime, datetime.datetime) and not isinstance(other, datetime.datetime):
            if cmp(self.dtime.date(), other) is 0:
                return -1
            else:
                return cmp(self.dtime.date(), other)
        else:
            return cmp(self.dtime, other)
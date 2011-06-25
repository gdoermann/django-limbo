from time import mktime
import datetime
import traceback
from copy import copy
import logging
from limbo.models import model_attribute

log = logging.getLogger(__file__)

def to_date(dtime):
    """ Takes a date or datetime object and returns the date
    portion of it """
    if isinstance(dtime, datetime.datetime):
        return dtime.date()
    else:
        return dtime

def get_first_dow(dtime):
    # TODO: Handle calendar dates that do not start on monday
    day = dtime - datetime.timedelta(days=dtime.weekday())
    return to_date(day)

def get_last_dow(dtime):
    # TODO: Handle calendar dates that do not start on monday
    days_diff = 7 - dtime.weekday()
    if days_diff == 7:
        return to_date(dtime)
    day = dtime + datetime.timedelta(days=days_diff)
    return to_date(day)

def check_datetime_date(start, end):
    """ Takes either a date or datetime. Verifies the two types are the same, else it returns the dates."""
    if type(start) is datetime.date and type(end) is not datetime.date:
        end = end.date()
    elif type(end) is datetime.date and type(start) is not datetime.date:
        start = start.date()
    return start, end

def parse_datetime(stamp, safe = True):
    try:
        if not isinstance(stamp, datetime.date):
            return datetime.datetime.fromtimestamp(float(stamp)).date()
        else:
            return stamp
    except (TypeError, ValueError), e:
        log.debug(traceback.format_exc())
        if not safe:
            raise e

def get_start_end(start = None, end = None, safe = True):
    """ Gets the start date and the end date for a given period.
    Defaults to this week.
    Makes sure the start is before the end date
    Verifies the start and end are the same type
    Takes None, datetime, date, or timestamps as inputs
    """
    now = datetime.datetime.now()
    tw_start = get_first_dow(now)
    tw_end = get_last_dow(now)
    
    parsed_start = parse_datetime(start, safe)
    parsed_end = parse_datetime(end, safe)

    if parsed_start:
        start = parsed_start
    if parsed_end:
        end = parsed_end

    if not start and end:
        start = end - datetime.timedelta(days=7)
    elif not end and start:
        end = start + datetime.timedelta(days=7)
    elif not end and not start:
        start = tw_start
        end = tw_end

    start, end = check_datetime_date(start, end)
    if start > end:
        return end, start
    return start, end

def get_request_start_end(request, start_key = 'start', end_key = 'end'):
    start = end = data = None
    if request.method == 'GET':
        data = request.GET
    elif request.method == 'POST':
        data = request.POST
    if data:
        start = data.get(start_key, None)
        end = data.get(end_key, None)
    return get_start_end(start, end)

def datetime_timestamp(dtime):
    """ Returns the float timestamp of the given date or datetime """
    return mktime(dtime.timetuple())

def datetime_timestamp_string(dtime):
    """ Returns the string timestamp of the given date or datetime """
    return repr(datetime_timestamp(dtime))


def get_datetimes(start, end):
    """ Returns a list of date objects within the time period """
    start, end = get_start_end(start, end)
    if isinstance(start, datetime.datetime):
        start = start.date()
    if isinstance(end, datetime.datetime):
        end = end.date()
    dates = []
    diff = end - start
    for day in range(diff.days+1):
        dates.append(start + datetime.timedelta(days=day))
    return dates

def update_month(dtime, offset):
    """ Be able to add or subtract months to a date/datetime object """
    sign = 1
    if offset < 0:
        sign = -1
    offset = abs(offset)
    years = offset//12
    months = offset%12
    raw_new_month = months * sign + dtime.month
    if raw_new_month == 0:
        years -= 1 * sign
    if raw_new_month > 12:
        years += 1 * sign
    new_year = years * sign + dtime.year
    new_month = raw_new_month%12 or 12
    new_dtime = copy(dtime)
    try:
        return new_dtime.replace(year = new_year, month = new_month)
    except ValueError:
        return new_dtime.replace(year = new_year, month = new_month+1, day=1) - datetime.timedelta(days=1)

def update_year(dtime, offset):
    """ Be able to add or subtract years to a date/datetime object """
    try:
        new_date = datetime.date(dtime.year + offset, dtime.month, dtime.day)
    except ValueError:
        # Handle Leap year
        new_date = datetime.date(dtime.year + offset, dtime.month, dtime.day-1)
    if isinstance(dtime, datetime.datetime):
        return datetime.datetime.combine(new_date, dtime.time())
    else:
        return new_date


def flattened_queryset_timeblocks(queryset, start_key, end_key):
    from limbo.timeblock.logic import TimeBlock
    queryset = queryset.order_by(start_key)
    timeblocks = []
    current_tb = None
    for obj in queryset:
        start = model_attribute(obj, start_key)
        end = model_attribute(obj, end_key)
        if not end:
            end = datetime.datetime.now()
        timeblock = TimeBlock(start, end)

        if current_tb:
            if timeblock.overlaps(current_tb):
                current_tb += timeblock
            else:
                timeblocks.append(current_tb)
                current_tb = timeblock
        else:
            current_tb = timeblock
    if current_tb:
        timeblocks.append(current_tb)
    return timeblocks

def flattened_duration(queryset, start_key, end_key):
    blocks = flattened_queryset_timeblocks(queryset, start_key, end_key)
    duration = datetime.timedelta()
    for block in blocks:
        duration += block.duration
    return duration

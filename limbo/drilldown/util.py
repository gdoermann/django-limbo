import calendar
from copy import copy
import re
import traceback
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils import dates
from limbo.drilldown.calcs import year_options, month_options, day_options
from django.db import models
from django import template
import logging

log = logging.getLogger(__file__)

class_div = "<div class='%s'>%%s</div>"
class_span = "<span class='%s'>%%s</span>"
link_tag = "<a href='%s'>%s</a>"

year_regex = re.compile('(1|2)\d{3}')
month_regex = re.compile('\d{1,2}')
day_regex = re.compile('\d{1,2}')



class OptionalDate:
    def __init__(self, year = None, month = None, day = None):
        self.year = year
        self.month = month
        self.day = day

class DateDrillDown(template.Node):
    MONTH_INTEGER = 'integer'
    MONTH_STR = 'string'
    month_type = MONTH_INTEGER
    context = None

    def __init__(self, object_name, date_attr = 'date'):
        self.object_name = object_name
        self.date_attr = date_attr

    def parse_request(self, context):
        self.request = None
        for dict in context.dicts:
            if dict.has_key('request'):
                self.request = dict.get('request')
                return

    def years(self):
        return year_options(self.objects, 'date', self.max_years)

    def months(self, year):
        return month_options(self.objects, year, 'date')

    def days(self, year, month):
        return day_options(self.objects, year, month, 'date')

    @property
    def objects(self):
        obj = self.date_object
        if isinstance(obj, models.Model):
            obj = obj.objects.all()
        elif isinstance(obj, models.Manager):
            obj = obj.all()
        return obj

    @property
    def object(self):
        if not self.context:
            return None
        if not getattr(self, '_object', None):
            for c in self.context:
                if c.has_key(self.object_name):
                    self._object = c.get(self.object_name)
                    break
        return getattr(self, '_object', None)

    @property
    def date_object(self):
        return getattr(self.object, self.date_attr, None)

    def parse_date(self, path):
        self.year_index = None
        self.month_index = None
        self.day_index = None

        year = None
        month = None
        day = None
        if path.endswith('/'):
            path = path[:-1]
        self.path_parts = path.split('/')
        # Parse the date
        index = -1
        for part in self.path_parts:
            index += 1
            if not self.year_index:
                if year_regex.match(part):
                    self.year_index = index
                    year = int(part)
            else: # Year has been parsed, look for month
                if not self.month_index:
                    if month_regex.match(part):
                        self.month_index = index
                        month = int(part)
                        self.month_type = self.MONTH_INTEGER
                    elif part in dates.MONTHS_3_REV.keys():
                        self.month_index = index
                        month = dates.MONTHS_3_REV[part]
                        self.month_type = self.MONTH_STR
                else:
                    if day_regex.match(part):
                        self.day_index = index
                        day = int(part)
                        break

        self.date = OptionalDate(year, month, day)

    def parse_date_lists(self, context):
        self.context = context
        years = self.years()
        months = []
        days = []
        if self.date.year and self.months(self.date.year):
            months = self.months(self.date.year)
        if self.date.year and self.date.month and self.days(self.date.year, self.date.month):
            days = self.days(self.date.year, self.date.month)
        return years, months, days


    def max_years(self):
        if self.context:
            return self.context.get('max_years', getattr(settings, 'MAX_YEARS', None))

    def get_month(self, month):
        if month and self.month_type == self.MONTH_STR:
            return dates.MONTHS_3_REV[int(month)]
        return month

    def get_readable_month(self, month):
        if month and month in dates.MONTHS_AP.keys():
            return dates.MONTHS_AP[month]
        if month and month in dates.MONTHS_3_REV.keys():
            return dates.MONTHS_AP[dates.MONTHS_3_REV[month]]
        return month

    def get_link(self, year = None, month = None, day = None):
        path_parts = copy(self.path_parts)
        year = year or self.date.year
        if day and not month:
            month = self.date.month
        month = self.get_month(month)
        if year != self.date.year:
            month = day = None
        elif self.get_month(self.date.month) != month:
            day = None

        if day:
            if self.day_index:
                path_parts[self.day_index] = str(day)
            else:
                path_parts.append(str(day))
        elif self.day_index:
            path_parts.pop(self.day_index)

        if month:
            if self.month_index:
                path_parts[self.month_index] = str(month)
            else:
                path_parts.append(str(month))
        elif self.month_index:
            path_parts.pop(self.month_index)

        if year:
            if self.year_index:
                path_parts[self.year_index] = str(year)
            else:
                path_parts.append(str(year))

        return '/'.join(path_parts) + '/'

    def render(self, context):
        try:
            self.context = context
            self.parse_request(context)
            path = self.request.META['PATH_INFO']
            self.parse_date(path)

            years, months, days = self.parse_date_lists(context)

            root_div = class_div % 'dd_date'
            root_parts = []

            year_div = class_div % 'dd_year'
            yr_spans = []
            yr_span = class_span % 'dd_yr'
            yr_span_disabled = class_span % 'dd_yr dd_disabled'
            yr_span_selected = class_span % 'dd_yr dd_selected'
            if years:
                all_years = list(range(min(years), max(years) + 1))
            else:
                all_years = years
            for year in all_years:
                if year == self.date.year or year in years:
                    ystr = link_tag %(self.get_link(year), year)
                    if year == self.date.year:
                        yr_spans.append(yr_span_selected % ystr)
                    else:
                        yr_spans.append(yr_span % ystr)
                else:
                    ystr = str(year)
                    yr_spans.append(yr_span_disabled % ystr)
            year_div  %= ''.join(yr_spans)
            root_parts.append(year_div)

            if self.date.year and self.months(self.date.year):
                month_div = class_div % 'dd_month'
                mo_span = class_span % 'dd_mo'
                mo_span_disabled = class_span % 'dd_mo dd_disabled'
                mo_span_selected = class_span % 'dd_mo dd_selected'
                mo_spans = []
                all_months = list([i+1 for i in range(12)])
                for month in list(all_months):
                    mstr = self.get_readable_month(month)
                    if month == self.date.month or month in months:
                        link = link_tag %(self.get_link(month = month), unicode(mstr))
                        if self.date.month == month:
                            mo_spans.append(mo_span_selected % link)
                        else:
                            mo_spans.append(mo_span % link)
                    else:
                        mo_spans.append(mo_span_disabled % unicode(mstr))
                month_div %= ''.join(mo_spans)
                root_parts.append(month_div)

            if self.date.year and self.date.month and self.days(self.date.year, self.date.month):
                day_div = class_div % 'dd_day'
                dy_span = class_span % 'dd_dy'
                dy_span_disabled = class_span % 'dd_dy dd_disabled'
                dy_span_selected = class_span % 'dd_dy dd_selected'
                day_spans = []

                all_days = list([i+1 for i in range(max(max(calendar.monthcalendar(self.date.year, self.date.month))))])
                for day in list(all_days):
                    if day != self.date.day and day in days:
                        day_spans.append(dy_span % link_tag %(self.get_link(day = day), day))
                    else:
                        if self.date.day == day:
                            day_spans.append(dy_span_selected % day)
                        else:
                            day_spans.append(dy_span_disabled % day)
                day_div %= ''.join(day_spans)
                root_parts.append(day_div)

            root_div %= ''.join(root_parts)
            return mark_safe(root_div)
        except:
            log.error(traceback.format_exc())
            return ''


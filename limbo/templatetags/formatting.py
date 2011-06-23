import datetime
from decimal import Decimal, InvalidOperation
import locale
from django.utils.safestring import mark_safe

locale.setlocale(locale.LC_ALL, '')
from django import template

register = template.Library()

def number(value, digits = 2):
    if value is None:
        return ''
    try:
        if callable(value):
            value = value()
        return locale.format('%%.%if' % digits, value, grouping=True, monetary=False)
    except Exception:
        return value
register.filter_function(number)

class generic_formatter:
    def __init__(self, method, digits=2):
        self.digits = digits
        self.method = method

    def __call__(self, value):
        return self.method(value, self.digits)

class number_formatter(generic_formatter):
    def __init__(self, digits=2):
        self.method = number
        self.digits = digits

def integer(value):
    return number(value, 0)
register.filter_function(integer)

def timedelta_to_hours(value):
    if not value:
        return 0
    days = Decimal(value.days)
    seconds = Decimal(value.seconds)
    return days *24 + seconds/3600
register.filter("timedelta_hours", timedelta_to_hours)

def hours_to_timedelta(value):
    if value is None:
        return value
    try:
        d = float(value)
    except Exception:
        return value
    delta = datetime.timedelta(hours=d)
    return delta

def hours(value):
    """Formats a time according to the given format."""
    if value in (None, u''):
        return u''
    try:
        return integer(timedelta_to_hours(value))
    except Exception:
        return value
hours.is_safe = False
register.filter_function(hours)

def percent(value, digits = 2):
    try:
        pct = Decimal(str(value)) * Decimal(100)
        return '%s %%' %number(pct, digits = digits)
    except (ArithmeticError, TypeError, ValueError):
        return value
register.filter_function(percent)

class percent_formatter(generic_formatter):
    def __init__(self, digits=2):
        self.method = percent
        self.digits = digits

def boolean_icon(value):
    from limbo.apps.datatables.rendering import BooleanRenderer
    v = bool(value)
    return BooleanRenderer.render_bool(v)
register.filter_function(boolean_icon)

def to_list(value):
    if not value:
        return ''
    values = str(value).split('\n')
    new_values = []
    sub_list = []
    for value in values:
        if not value.strip():
            continue
        if value.startswith('\t'):
            value = '<li>%s</li>' %value.replace('\t', '')
            sub_list.append(value)
        else:
            if sub_list:
                new_values.append('<ul>%s</ul>' %''.join(sub_list))
                sub_list = []
            new_values.append('<li>%s</li>'%value)
    return mark_safe('<ul>%s</ul>' %''.join(new_values))
register.filter_function(to_list)

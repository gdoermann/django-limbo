from copy import copy
from django.conf import settings
from django.forms import fields, models, ValidationError
from django.forms.util import ValidationError
from django.template.defaultfilters import slugify
from django.utils.formats import get_format
from django.utils.translation import ugettext_lazy as _
from limbo import widgets
from limbo.timeblock.logic import TimeBlock
from limbo.validation import valid_sms, clean_sms
import datetime

DEFAULT_DATE_INPUT_FORMATS = get_format('DATE_INPUT_FORMATS')
DEFAULT_TIME_INPUT_FORMATS = get_format('TIME_INPUT_FORMATS')

class MoneyField(fields.DecimalField):

    def clean(self, value):
        if isinstance(value, basestring):
            value = value.replace('$', '')
        return super(MoneyField, self).clean(value)

class MobileField(fields.CharField):
    default_error_messages = {
        'invalid': _(u'Invalid Mobile Number.'),
    }

    def __init__(self, max_length=20, min_length=None, *args, **kwargs):
        self.max_length, self.min_length = max_length, min_length
        super(MobileField, self).__init__(*args, **kwargs)

        defaults = copy(fields.CharField.default_error_messages)
        defaults.update(self.default_error_messages)
        self.default_error_messages = defaults

    def clean(self, value):
        value = super(MobileField, self).clean(value)
        if not value:
            return value
        if not valid_sms(value):
            raise ValidationError(self.error_messages['invalid'])
        return clean_sms(value)

class ParsedChoiceField(fields.ChoiceField):
    DEFAULT_PARSERS = list()

    def __init__(self, *args, **kwargs):
        self.parsers = list(kwargs.pop('parsers', [])) + list(self.DEFAULT_PARSERS)
        super(ParsedChoiceField, self).__init__(*args, **kwargs)

    def parse_value(self, value):
        for parser in self.parsers:
            parsed = parser(value, self.choices)
            if parsed:
                return parsed
        return value

    def clean(self, value):
        value = self.parse_value(value)
        value = self.to_python(value)
        self.validate(value)
        self.run_validators(value)
        return value

class UploadChoiceField(ParsedChoiceField):
    DEFAULT_PARSERS = (widgets.stripped_reverse_choice,)
    widget = widgets.CheckedSelect

    @classmethod
    def from_choice_field(cls, field, widget=widgets.CheckedSelect):
        return cls(field.choices, field.required, widget, field.label,
                 field.initial, field.help_text,
                 error_messages=field.error_messages, show_hidden_initial=field.show_hidden_initial,
                 validators=field.validators, localize=field.localize)

class ModelUploadChoiceField(models.ModelChoiceField, UploadChoiceField):
    DEFAULT_PARSERS = UploadChoiceField.DEFAULT_PARSERS

    def __init__(self, *args, **kwargs):
        self.parsers = list(kwargs.pop('parsers', [])) + list(self.DEFAULT_PARSERS)
        models.ModelChoiceField.__init__(self, *args, **kwargs)

    def clean(self, value):
        return UploadChoiceField.clean(self, value)

    @classmethod
    def from_model_choice_field(cls, field, widget=widgets.CheckedSelect):
        return cls(field.queryset, field.empty_label, field.cache_choices,
                 field.required, widget, field.label, field.initial,
                 field.help_text, field.to_field_name,
                 error_messages=field.error_messages, show_hidden_initial=field.show_hidden_initial,
                 validators=field.validators, localize=field.localize)

class YearField(fields.DateField):
    DEFAULT_YEAR_INPUT_FORMATS = list(DEFAULT_DATE_INPUT_FORMATS) + ['%Y', '%y']
    def __init__(self, input_formats=DEFAULT_YEAR_INPUT_FORMATS, *args, **kwargs):
        super(YearField, self).__init__(*args, **kwargs)
        self.input_formats = input_formats

    def clean(self, value):
        value = super(YearField, self).clean(value)
        return value and value.year or value

time_formats = []
try:
    time_formats += list(get_format('DEFAULT_TIME_INPUT_FORMATS'))
except AttributeError:
    pass

DEFAULT_TIME_INPUT_FORMATS = getattr(settings, 'DEFAULT_TIME_INPUT_FORMATS',
      [
          '%H:%M %p',
          '%H:%M:%S %p'
      ] + time_formats )

class AutoTimeField(fields.TimeField):
    widget = widgets.TimePicker

    def __init__(self, input_formats=DEFAULT_TIME_INPUT_FORMATS, *args, **kwargs):
        super(AutoTimeField, self).__init__(*args, **kwargs)
        self.input_formats = input_formats

class AutoDateField(fields.DateField):
    widget = widgets.DatePicker

    def __init__(self, input_formats=DEFAULT_DATE_INPUT_FORMATS, *args, **kwargs):
        super(AutoDateField, self).__init__(*args, **kwargs)
        self.input_formats = input_formats

class TimeRange:
    def __init__(self, start, end):
        self.start = start
        self.end = end

    @property
    def delta(self):
        if not (self.start and self.end):
            return datetime.timedelta()
        return self.end - self.start

class TimeRangePicker(fields.ChoiceField):
    widget = widgets.TimeRange

    class DEFAULT_CHOICES:
        TODAY = 'today'
        YESTERDAY = 'yesterday'
        THIS_WEEK = 'this_week'
        LAST_WEEK = 'last_week'
        THIS_MONTH = 'this_month'
        LAST_MONTH = 'last_month'
        ALL_TIME = 'all_time'
        CHOICES = (
            (TODAY, 'Today'),
            (YESTERDAY, 'Yesterday'),
            (THIS_WEEK, 'This Week'),
            (LAST_WEEK, 'Last Week'),
            (THIS_MONTH, 'This Month'),
            (LAST_MONTH, 'Last Month'),
        )
        ADMIN_CHOICES = tuple(list(CHOICES) +
            [
                (ALL_TIME, 'All Time'),
            ]
        )

    def __init__(self, choices = DEFAULT_CHOICES.CHOICES, *args, **kwargs):
        if not choices:
            choices = self.DEFAULT_CHOICES.CHOICES
        super(TimeRangePicker, self).__init__(choices, *args, **kwargs)


    def clean(self, value):
        value = super(TimeRangePicker, self).clean(value)
        return self.convert_date(value)

    @classmethod
    def default_range(cls, value = DEFAULT_CHOICES.TODAY):
        now = datetime.datetime.now()
        one_day = datetime.timedelta(days=1)
        one_week = datetime.timedelta(weeks=1)
        first_dom = datetime.datetime(year=now.year, month=now.month, day=1)
        midnight = datetime.time(0,0)
        minute = datetime.timedelta(minutes=1)
        today = datetime.datetime.combine(now.date(), midnight)
        days_from_sunday = one_day * (today.weekday()+1)
        days_to_sunday = one_day * (6-today.weekday())
        if value == cls.DEFAULT_CHOICES.TODAY:
            return TimeRange(today, now)
        elif value == cls.DEFAULT_CHOICES.YESTERDAY:
            return TimeRange(today - one_day, today-minute)
        elif value == cls.DEFAULT_CHOICES.THIS_WEEK:
            return TimeRange(today - days_from_sunday, now)
        elif value == cls.DEFAULT_CHOICES.LAST_WEEK:
            return TimeRange(today - one_week - days_from_sunday, today - one_week -minute + days_to_sunday)
        elif value == cls.DEFAULT_CHOICES.THIS_MONTH:
            return TimeRange(first_dom, now)
        elif value == cls.DEFAULT_CHOICES.LAST_MONTH:
            ldolm = first_dom - minute
            fdolm = datetime.datetime(year=ldolm.year, month=ldolm.month, day=1)
            return TimeRange(fdolm, ldolm)
        elif value == cls.DEFAULT_CHOICES.ALL_TIME:
            return TimeRange(None, None)

    def convert_date(self, value):
        return self.default_range(value)

def check_required(kwargs):
    kwargs['required'] = kwargs.get('required', False)

class DateRangeFieldGenerator:
    """ This is not an actual field, but a field generator """
    DEFAULT_MAX_RANGE = datetime.timedelta(weeks=52)
    @classmethod
    def fields(cls, **kwargs):
        """ Returns 3 fields, a Button set quick picker, a start date time field, and an end date time field"""

        # This removes stuff from kwargs and should happen first
        start, end = cls.start_end(**kwargs)
        picker = cls.picker(**kwargs)
        return picker, start, end

    @classmethod
    def picker(cls, **kwargs):
        check_required(kwargs)
        return TimeRangePicker(**kwargs)

    @classmethod
    def __dtfield(cls, label, class_name, **kwargs):
        new_kwargs = {}
        new_kwargs.update(kwargs)
        new_kwargs['label'] = label
        field = AutoDateField(**new_kwargs)
        field.widget.addClass(class_name)
        return field

    @classmethod
    def start(cls, **kwargs):
        check_required(kwargs)
        label = kwargs.pop('start_label', "Start Date")
        return cls.__dtfield(label, 'start_date', **kwargs)

    @classmethod
    def end(cls, **kwargs):
        check_required(kwargs)
        label = kwargs.pop('end_label', "End Date")
        return cls.__dtfield(label, 'end_date', **kwargs)

    @classmethod
    def start_end(cls, **kwargs):
        return cls.start(**kwargs), cls.end(**kwargs)

    @classmethod
    def clean(cls,
              data,
              picker_key = 'picker',
              start_date = 'start_date',
              end_date = 'end_date',
              max_range = None,
              default_range = None,
              required=True):
        """ This required specifies if the range is required, so a start and end
            must be specified in the end

        @type default_range: TimeRange or timedelta
        @type max_range: timedelta
        """
        if callable(default_range):
            default_range = default_range()
        if isinstance(default_range, datetime.timedelta):
            now = datetime.datetime.now()
            default_range = TimeRange(now - default_range, now)
        requireds = [start_date, end_date, picker_key]
        for key in requireds:
            if not data.has_key(key):
                data[key] = ''
        start = data[start_date]
        end = data[end_date]
        picker = data[picker_key]
        if not picker and not (start or end):
            if required and not default_range:
                raise ValidationError("You must use the picker or specify a start and end date.")
            elif default_range:
                end = default_range.end
                start = default_range.start
            else:
                return data
        if not start:
            start = picker.start
        if not end:
            end = picker.end
        if required and not (start and end):
            if not (isinstance(picker, TimeRange) and picker.start is None and picker.end is None):
                # If picker was chosen and all time is a valid option, it will return none as start and end
                raise ValidationError('Date range required: %s - %s' %(start_date, end_date))
        if  start and end:
            tb = TimeBlock(start, end)
            start, end = tb.start, tb.end
            if start > end:
                raise ValidationError('Start date must be before end date.')
            elif max_range and end - start > max_range:
                raise ValidationError('Time range too large.  Max range:%s' %cls.get_max_range_display(max_range))
        data[start_date] = start
        data[end_date] = end
        return data

    @classmethod
    def get_max_range_display(cls, max_range):
        # TODO: Actually format this
        return str(max_range)

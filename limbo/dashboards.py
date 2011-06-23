from django.core.urlresolvers import reverse
from django.template.defaultfilters import title
from limbo.ajax import json_response
from limbo import forms
from limbo.strings import unslugify
import datetime

class DashboardForm(forms.Form):
    picker = forms.DateRangeFieldGenerator.picker(initial = forms.TimeRangePicker.DEFAULT_CHOICES.TODAY)
    start_date, end_date = forms.DateRangeFieldGenerator.start_end()

    def __init__(self, max_range = datetime.timedelta(weeks=4),
             default_range = forms.TimeRangePicker.default_range, *args, **kwargs):
        super(DashboardForm, self).__init__(*args, **kwargs)
        self.max_range = max_range
        self.default_range = default_range

    @property
    def start(self):
        if self.is_valid():
            sdate = self.cleaned_data['start_date']
            if not isinstance(sdate, datetime.datetime) and isinstance(sdate, datetime.date):
                sdate = datetime.datetime.combine(sdate, datetime.time())
            return sdate

    @property
    def end(self):
        if self.is_valid():
            edate = self.cleaned_data['end_date']
            if not isinstance(edate, datetime.datetime) and isinstance(edate, datetime.date):
                edate = datetime.datetime.combine(edate, datetime.time(23,59,59))
            return edate

    def clean(self):
        return forms.DateRangeFieldGenerator.clean(
                self.cleaned_data,
                start_date='start_date',
                end_date='end_date',
                max_range=self.max_range,
                default_range=self.default_range,
                required=False)

class DashboardWidget():
    def __init__(self, attr, formatter = None, perm = None, request_test = None):
        """ Formatter is a callable funtion that will
        format the given value (like a template filter)"""
        self.name = attr
        self.formatter = formatter
        self.perm = perm
        self.request_test = request_test

    def has_access(self, request):
        if not self.perm and not self.request_test:
            return True
        elif self.perm and request.user.has_perm(self.perm):
            return True
        elif self.request_test and self.request_test(request):
            return True
        else:
            return False

    def __call__(self, model):
        return BoundDashboardWidget(self.name, model, self.formatter)

class BoundDashboardWidget():
    def __init__(self, attr, model, formatter = None):
        """ Formatter is a callable funtion that will
        format the given value (like a template filter)"""
        self.model = model
        self.name = attr
        self.formatter = formatter

    @property
    def title(self):
        return getattr(self.attr, 'short_description', unslugify(title(self.name)))

    @property
    def description(self):
        return getattr(self.attr, 'description', '')

    @property
    def attr(self):
        return getattr(self.model, self.name, None)

    def value(self, start = None, end = None):
        if callable(self.attr):
            v = self.attr(start, end)
        else:
            v = self.attr
        if self.formatter:
            return self.formatter(v)
        else:
            return v

    def __unicode__(self):
        return unicode(self.value)

class Dashboard:
    # TODO: make this like forms where the widgets are auto detected.
    WIDGETS = []
    MAX_RANGE = datetime.timedelta(days=35)
    DEFAULT_RANGE = forms.TimeRangePicker.default_range
    viewname = None

    def __init__(self, request, object):
        self.request = request
        self.object = object
        data = {}
        data.update(request.REQUEST)
        if not request.user.is_superuser:
            max_range = self.MAX_RANGE
        else:
            max_range = None
        form = DashboardForm(max_range, self.DEFAULT_RANGE, data)
        if form.is_valid():
            start = form.start
            end = form.end
        else:
            if self.DEFAULT_RANGE is not None:
                start = datetime.datetime.now() - self.DEFAULT_RANGE
                end = datetime.datetime.now()
            else:
                start = None
                end = None
        self.start = start
        self.end = end

    def view_args(self):
        return list()

    def view_kwargs(self):
        return dict()

    def href(self):
        return reverse(self.viewname, args = self.view_args(), kwargs = self.view_kwargs())

    @property
    def widgets(self):
        widgets = []
        for widget in self.WIDGETS:
            if widget.has_access(self.request):
                widgets.append(widget(self.object))
        return widgets

    def response(self):
        context = {
            'start':str(self.start),
            'end':str(self.end),
        }
        for widget in self.widgets:
            context[widget.name] = str(widget.value(self.start, self.end))
        return json_response(context)

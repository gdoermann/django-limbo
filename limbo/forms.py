""" Now you can just call the limbo.forms and get everything that is also in django.forms """
import collections
from copy import deepcopy
import csv
from StringIO import StringIO
from django.forms import *
from django.forms import formsets
from django.forms.formsets import formset_factory
from django.utils.datastructures import SortedDict
from django.utils.encoding import StrAndUnicode
from limbo.fields import *
from limbo.widgets import *

Choice = collections.namedtuple("Choice", ['value', 'display'])

def form_data(form):
    data = SortedDict()
    prefix = form.prefix and '%s-' %form.prefix or ''
    for key in form.fields.keys():
        data[key] = form.data.get('%s%s' %(prefix, key), None)
    return data


class ContingentForms(dict):
    def __init__(self, request, seq=None, **kwargs):
        self.request = request

    def append(self, field, url, permission = None):
        if not permission or self.request.user.has_perm(permission):
            self[field] = url

class WidgetSetter:

    def map_widget_defaults(self, include=None, exclude=[]):
        self.map_widgets(SelectMultiple, AdvancedMultiSelect, include, exclude)
        self.map_widgets(Select, Combobox, include, exclude)
        self.map_widgets(Textarea, AutoResizeTextarea, include, exclude)
        self.map_widgets(DateInput, DatePicker, include, exclude)

    def map_widgets(self, from_widget, to_widget, include=None, exclude=[]):
        for name, field in self.fields.items():
            if include is not None and name not in include:
                continue
            elif exclude and name in exclude:
                continue
            # We DON'T want isinstance
            fw = callable(from_widget) and from_widget() or from_widget
            if type(fw) == type(field.widget):
                self.set_widget(name, to_widget)

    def set_widget(self, name, widget):
        if self.fields.has_key(name):
            if callable(widget):
                widget = widget()
            old_w = self.fields[name].widget
            if hasattr(old_w, 'choices'):
                widget.choices = old_w.choices
            self.fields[name].widget = widget

class CSVFormSet(formsets.BaseFormSet):
    def __init__(self, dict_reader = None, headers = None, data=None, *args, **kwargs):
        self.check_meta()
        self.headers = headers
        self.actual_headers = headers
        self.prefix=kwargs.get('prefix', None)
        if dict_reader:
            if not data or not data.has_key(self.add_field_prefix(formsets.TOTAL_FORM_COUNT)):
                data = self.data_from_csv(dict_reader)
        super(CSVFormSet, self).__init__(data, *args, **kwargs)

    def check_meta(self, obj = None):
        if not obj:
            obj = self
        if not hasattr(obj, 'Meta'):
            class Meta:
                pass
            obj.Meta = Meta

    def data_from_csv(self, dict_reader):
        data = {}
        if not isinstance(dict_reader, csv.DictReader):
            dict_reader = csv.DictReader(dict_reader)
        fieldname_map = self.fieldname_map(dict_reader.fieldnames)
        self.actual_headers = fieldname_map.values()
        line_num = 0
        for line in dict_reader:
            for key, value in line.items():
                if fieldname_map.has_key(key):
                    fieldname = self.full_fieldname(line_num, fieldname_map[key])
                    data[fieldname] = value
            line_num += 1
        management = {
            self.add_field_prefix(formsets.TOTAL_FORM_COUNT): line_num,
            self.add_field_prefix(formsets.INITIAL_FORM_COUNT): line_num,
            self.add_field_prefix(formsets.MAX_NUM_FORM_COUNT): line_num
        }
        data.update(management)
        return data

    def add_field_prefix(self, fieldname):
        return self.prefix and '%s-%s' % (self.prefix, fieldname) or fieldname

    def full_fieldname(self, index, fieldname):
        full_name = '%s-%s' %(index, fieldname)
        return self.add_field_prefix(full_name)

    def fieldname_map(self, actual_names):
        if not actual_names:
            return dict([(name, name) for name in self.headers])
        map = SortedDict()
        from django.template.defaultfilters import slugify
        for header in self.headers:
            for name in actual_names:
                if slugify(name) == slugify(header):
                    map[name] = header
                    continue
        self.Meta.fields = map.values()
        meta = deepcopy(self.form.Meta)
        meta.fields = self.Meta.fields
        attrs = {'Meta': meta}
        self.form = type('Dynamic' + self.form.__name__, (self.form,), attrs)
        return map

    def valid_forms(self):
        forms = []
        if not self.is_bound:
            return forms
        for form in self.forms:
            if form.is_valid():
                forms.append(form)
        return forms

    def invalid_forms(self):
        forms = []
        if not self.is_bound:
            return forms
        for form in self.forms:
            if not form.is_valid():
                forms.append(form)
        return forms

    def _csv_writer(self):
        f = StringIO()
        writer = csv.DictWriter(f, self.headers)
        writer.writerow(SortedDict([(name, name) for name in self.headers]))
        return f, writer

    def valid_csv(self):
        if not self.is_bound:
            return None
        self.is_valid() # just run validation
        f, writer = self._csv_writer()
        for form in self.valid_forms():
            self.write_form(writer, form)
        f.seek(0)
        return f

    def invalid_csv(self):
        if not self.is_bound:
            return None
        self.is_valid() # just run validation
        f, writer = self._csv_writer()
        for form in self.invalid_forms():
            self.write_form(writer, form)
        f.seek(0)
        return f

    def write_form(self, writer, form):
        def reformat(value):
            if hasattr(value, 'pk'):
                return value.pk
            else:
                return value

        data = {}
        if form.is_valid():
            raw_data = form.cleaned_data
        else:
            raw_data = form_data(form)

        for key, value in raw_data.items():
            data[key] = reformat(value)
        writer.writerow(data)


class DateFilterForm(Form, WidgetSetter):
    def __init__(self, *args, **kwargs):
        self.max_range = kwargs.pop('max_range', datetime.timedelta(days=32))
        super(DateFilterForm, self).__init__(*args, **kwargs)
        self.map_widget_defaults()

    picker = DateRangeFieldGenerator.picker(initial=TimeRangePicker.DEFAULT_CHOICES.TODAY)
    start_date, end_date = DateRangeFieldGenerator.start_end()

    @property
    def start(self):
        start = self.is_valid() and self.cleaned_data['start_date'] or None
        if start:
            start = datetime.datetime.combine(start, datetime.time(0))
        return start

    @property
    def end(self):
        end = self.is_valid() and self.cleaned_data['end_date'] or None
        if end:
            end = datetime.datetime.combine(end, datetime.time(23,59,59))
        return end

    def clean(self):
        data = DateRangeFieldGenerator.clean(self.cleaned_data, max_range=self.max_range,
                     default_range=TimeRangePicker.default_range(
                         TimeRangePicker.DEFAULT_CHOICES.TODAY))
        return data

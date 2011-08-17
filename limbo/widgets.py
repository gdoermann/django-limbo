from copy import copy
from django.forms import *
from django.forms import widgets
from django.utils import datetime_safe
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.template.defaultfilters import slugify
import traceback

class MultiClassWidget(Widget):
    classes = []
    def __init__(self, attrs = None, classes = []):
        self.classes += classes
        super(MultiClassWidget, self).__init__(attrs)
    
    def build_attrs(self, extra_attrs=None, **kwargs):
        classes = copy(self.classes)
        if 'class' in extra_attrs.keys():
            others = extra_attrs.pop('class')
            if isinstance(others, basestring):
                classes.append(others)
            else:
                # List or tuple
                classes += others
        kwargs['class'] = ' '.join(classes)
        return super(MultiClassWidget, self).build_attrs(extra_attrs, **kwargs)

    def _process_classes(self, cls, append_method):
        if isinstance(cls, basestring):
            append_method(cls)
        else:
            for item in cls:
                append_method(item)
    
    def addClass(self, cls):
        def append_cls(cls):
            if not self.hasClass(cls):
                self.classes.append(cls)
        self._process_classes(cls, append_cls)
    
    def removeClass(self, cls):
        def remove_cls(cls):
            if self.hasClass(cls):
                self.classes.remove(cls)
        self._process_classes(cls, remove_cls)
    
    def hasClass(self, cls):
        return cls in self.classes

class AutoComplete(MultiClassWidget, TextInput):
    classes = ['autocomplete']

class Combobox(Select, MultiClassWidget):
    classes = ['combobox']


def stripped_reverse_choice(value, choices):
    def strip(v):
        v = str(v)
        replace = ['-', '_', "'", '"']
        v = slugify(v)
        for i in replace:
            v = v.replace(i, '')
        return v.lower()
    stripped = strip(value)
    for choice, display in choices:
        if stripped == strip(choice):
            return choice
        if stripped == strip(display):
            return choice
    for choice, display in choices:
        if stripped in strip(choice):
            return choice
        if stripped in strip(display):
            return choice
    return value

class CheckedSelect(widgets.Select):
    def render(self, name, value, attrs=None, choices=()):
        ovalue = value
        value = stripped_reverse_choice(value, self.choices)
        return super(CheckedSelect, self).render(name, value, attrs=attrs, choices=choices)

DATE_PICKER_FORMAT = '%m/%d/%Y'     # '5/24/2010'

class DatePicker(MultiClassWidget, DateInput):
    format = DATE_PICKER_FORMAT
    
    def __init__(self, *args, **kwargs):
        self.classes = ['datepicker']
        format = self.format
        MultiClassWidget.__init__(self, *args, **kwargs)
        DateInput.__init__(self, *args, **kwargs)
        self.format = format

TIME_PICKER_FORMAT = '%H:%M %p'

class TimePicker(TimeInput, MultiClassWidget):
    format = TIME_PICKER_FORMAT
    
    def __init__(self, *args, **kwargs):
        self.classes = ['timepicker']
        format = self.format
        MultiClassWidget.__init__(self, *args, **kwargs)
        TimeInput.__init__(self, *args, **kwargs)
        self.format = format

    def _format_value(self, value):
        value = super(TimePicker, self)._format_value(value)
        return value.lower()

class AdvancedMultiSelect(SelectMultiple, MultiClassWidget):
    classes = ['multiselect']


class ButtonRadioInput(widgets.RadioInput):
    def __unicode__(self):
        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        choice_label = conditional_escape(force_unicode(self.choice_label))
        return mark_safe(u'<label%s>%s</label>%s' % (label_for, choice_label, self.tag()))

class ButtonSetRenderer(widgets.RadioFieldRenderer):
    WRAPPER = 'span'
    wrapper_attrs = {'class':'buttonset'}
    
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield ButtonRadioInput(self.name, self.value, self.attrs.copy(), choice, i)

    def __getitem__(self, idx):
        choice = self.choices[idx] # Let the IndexError propogate
        return ButtonRadioInput(self.name, self.value, self.attrs.copy(), choice, idx)

    def __unicode__(self):
        return self.render()
    
    def render(self):
        s = ''
        try:
            wattrs = '' 
            if self.wrapper_attrs:
                if not self.wrapper_attrs.has_key('id'):
                    self.wrapper_attrs['id'] = "buttonset"
                wattrs = ' '.join(['%s="%s"' %(key, value) for key, value in self.wrapper_attrs.items()])
            s += u'<%(wrapper)s %(attrs)s>\n%(items)s\n</%(wrapper)s>' %{
                              'wrapper':self.WRAPPER, 'attrs':wattrs,
                              'items': u'\n'.join([force_unicode(w) for w in self])}
        except Exception:
            traceback.print_exc()
        return mark_safe(s)

class ButtonSet(widgets.RadioSelect, MultiClassWidget):
    renderer = ButtonSetRenderer
    
    def id_for_label(self, id_):
        return id_
    
    def get_renderer(self, name, value, attrs=dict(), choices=()):
        renderer = widgets.RadioSelect.get_renderer(self, name, value, attrs, choices)
        if not self.attrs.has_key(id):
            self.attrs['id'] = self.id_for_label(name + '_buttonset')
        renderer.wrapper_attrs['id'] = self.id_for_label(self.attrs['id'])
        return renderer

class AutoResizeTextarea(MultiClassWidget, Textarea):
    def __init__(self, attrs=None, classes = ['autoresize']):
        self.classes = classes
        default_attrs = {'cols': '40', 'rows': '2'}
        if attrs:
            default_attrs.update(attrs)
        super(AutoResizeTextarea, self).__init__(default_attrs)

class TimeRangeRenderer(ButtonSetRenderer):
    wrapper_attrs = {'class':'buttonset range_picker'}

class TimeRange(ButtonSet):
    classes = ['time_option']
    renderer = TimeRangeRenderer

class RandomStringGenerator(MultiClassWidget, TextInput):
    classes = ['random_generator']
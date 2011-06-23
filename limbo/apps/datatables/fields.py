from django.template.defaultfilters import slugify
from limbo.meta import DeclaredField
from limbo.apps.datatables.rendering import *
from django.db.models import Q
from django.utils import simplejson
from django import forms
from django.core.validators import EMPTY_VALUES
from limbo.apps.datatables.util import test_rights
import datetime

class TableField(DeclaredField):
    """ This is a declared field table columns"""

class TableColumn(TableField):
    def __init__(self, attr,
                 label=None,
                 visible=True,
                 sortable=False,
                 searchable=False,
                 choices=None,
                 field=None,
                 renderer=CellRenderer(),
                 is_related=False,
                 request_test=None,
                 permission=None):
        self.label=label
        self.attr=attr
        self.visible=visible
        self.sortable=sortable
        self.searchable=searchable
        self.choices=choices
        self.set_field(field)
        self.renderer=renderer
        self.is_related=is_related
        self.request_test=request_test
        self.permission=permission
        TableField.__init__(self)

    def test(self, request):
        """ This cannot be simplified into a one liner... """
        return test_rights(request, self.request_test, self.permission)

    @property
    def id(self):
        return "search_%s" %slugify(self.label)

    @property
    def value(self):
        if self.choices:
            return None
        else:
            return "Search %s" %self.label

    @property
    def attrs(self):
        attrs = {
            'title':self.label,
        }
        return attrs

    def render(self, *args, **kwargs):
        renderer = self.renderer or CellRenderer()
        return renderer.render(*args, **kwargs)

    def properties(self):
        """Properties of the column for use in the javascript initialization"""
        return simplejson.dumps({
            "bTitle":self.label,
            "bSearchable":  self.searchable,
            "bVisible":     self.visible,
            "bSortable":    self.sortable,
        })

    def classes(self):
        cls_lst = [slugify(self.label),
           self.visible and "bVisible" or "nVisible",
           self.searchable and "bSearchable" or "nSearchable",
           self.sortable and "bSortable" or "nSortable",
       ]
        return ' '.join(cls_lst)

    def clean(self, value):
        try:
            if isinstance(value, unicode):
                value = str(value)
            return self.field.clean(value)
        except forms.ValidationError:
            return None

    _field = None
    def get_field(self):
        if not self.searchable:
            return forms.CharField(show_hidden_initial=True)
        if self._field:
            try:
                self._field.widget.choices = self.full_choices
            except Exception:
                pass
            return self._field
        elif self.choices is not None:
            return forms.ChoiceField(choices=self.full_choices, required=False)
        else:
            return forms.CharField(required=False)

    @property
    def full_choices(self):
        if not self.choices:
            if self._field and hasattr(self._field.widget, 'choices'):
                return self._field.widget.choices
            return None
        else:
            return [("None", 'All')] + list(self.choices)

    def set_field(self, field):
        if callable(field):
            field = field()
        self._field = field
    field = property(get_field, set_field)

    def widget(self):
        if not self.field:
            return ''
        args = (self.id, self.value, self.attrs)
        kwargs = {}
        return self.field.widget.render(*args, **kwargs)

    def sort(self, direction='asc'):
        if not self.sortable:
            return None
        name = self.attr
        if direction == 'desc':
            name = '-'+name
        return name

    def cleaned_value(self, value):
        value = self.clean(value)
        if value == "None" or value in EMPTY_VALUES:
            return None
        return value

    def filter(self, value):
        """ Must return a Q or None """
        if not self.searchable:
            return None
        value = self.cleaned_value(value)
        if value is None:
            return None
        if isinstance(value, (datetime.date, datetime.datetime)) or self.is_related:
            kwargz = {self.attr : value}
        elif isinstance(value, basestring):
            kwargz = {self.attr+"__icontains" : value}
        else:
            kwargz = {self.attr : value}
        return Q(**kwargz)

    def filter_queryset(self, queryset, value):
        # This is so you can do custom alterations to a queryset
        return queryset

class BooleanColumn(TableColumn):
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = kwargs.get('choices',(
                               ('1', "Yes"),
                               ('0', "No")
                               ))
        kwargs['field'] = kwargs.get('field', forms.NullBooleanField())
        kwargs['renderer'] = kwargs.get('renderer', BooleanRenderer())
        super(BooleanColumn, self).__init__(*args, **kwargs)

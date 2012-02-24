from django.db.models.query import QuerySet
from django.template.defaultfilters import slugify
from limbo.meta import DeclaredField
from limbo.apps.datatables.rendering import *
from django.db.models import Q
from django.utils import simplejson
from django import forms
from django.core.validators import EMPTY_VALUES
from limbo.apps.datatables.util import test_rights
import datetime
import logging

logger = logging.getLogger(__file__)

logger = logging.getLogger(__file__)

class TableField(DeclaredField):
    """ This is a declared field table columns"""

class TableColumn(TableField):
    DEFAULT_RENDERER = CellRenderer()
    def __init__(self, attr,
                 label=None,
                 visible=True,
                 sortable=False,
                 searchable=False,
                 choices=None,
                 field=None,
                 renderer=None,
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
        self.renderer=renderer or self.DEFAULT_RENDERER
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
        if not self.searchable:
            attrs['class'] = 'ui-helper-hidden'
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
            if dict(self.choices).has_key('None'):
                return self.choices
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

    def Q(self, value):
        """ Must return a Q or None """
        if not self.searchable:
            return None
        kwargs = self.filter_args(value)
        if not kwargs:
            return None
        else:
            return Q(**kwargs)

    def filter_args(self, value):
        cvalue = self.cleaned_value(value)
        if cvalue is None:
            return {}
        return {self.attr+"__icontains": cvalue}

    def filter_queryset(self, queryset, value):
        # This is so you can do custom alterations to a queryset
        args = self.filter_args(value)
        if not args:
            return queryset
        else:
            return queryset.filter(**args)

class SearchableTableColumn(TableColumn):
    def __init__(self, attr,
                 label=None,
                 visible=True,
                 sortable=False,
                 searchable=True,
                 choices=None,
                 field=None,
                 renderer=None,
                 is_related=False,
                 request_test=None,
                 permission=None):
        super(SearchableTableColumn, self).__init__(attr, label=label, visible=visible, sortable=sortable,
            searchable=searchable, choices=choices, field=field,
            renderer=renderer, is_related=is_related, request_test=request_test,
            permission=permission)

class CaseSensitiveTableColumn(SearchableTableColumn):
    def filter_args(self, value):
        cvalue = self.cleaned_value(value)
        if cvalue is None:
            return {}
        return {self.attr+"__contains": cvalue}

class ExactTableColumn(SearchableTableColumn):
    def filter_args(self, value):
        cvalue = self.cleaned_value(value)
        if cvalue is None:
            return {}
        return {self.attr+"__iexact": cvalue}

class BooleanSearchField(forms.NullBooleanField):
    def to_python(self, value):
        if value in ('2'):
            return True
        elif value in ('3'):
            return False
        else:
            return super(BooleanSearchField, self).to_python(value)

class BooleanColumn(TableColumn):
    DEFAULT_CHOICES = (
        ('None', 'All'),
        ('2', "Yes"),
        ('3', "No")
        )
    def __init__(self, *args, **kwargs):
        kwargs['choices'] = kwargs.get('choices', self.DEFAULT_CHOICES)
        kwargs['field'] = kwargs.get('field', BooleanSearchField())
        kwargs['renderer'] = kwargs.get('renderer', BooleanRenderer())
        super(BooleanColumn, self).__init__(*args, **kwargs)

class ModelTableColumn(TableColumn):
    def __init__(self, attr,
                 queryset=None,
                 sortable=True,
                 searchable=True,
                 filter_attribute=None,
                 *args, **kwargs):
        """
        @param queryset: A queryset of choices
        """
        kwargs['sortable'] = sortable
        kwargs['searchable'] = searchable
        super(ModelTableColumn, self).__init__(attr, *args, **kwargs)
        self.filter_attribute = filter_attribute or self.attr
        self._queryset = queryset
        self._parse_choices()

    @property
    def queryset(self):
        if not isinstance(self._queryset, QuerySet) and callable(self._queryset):
            return self._queryset(self)
        else:
            return self._queryset

    @queryset.setter
    def queryset(self, q):
        self._queryset = q
        self._parse_choices()

    def _parse_choices(self):
        if not self.queryset:
            return
        choices = []
        for item in self.queryset:
            choices.append([item.pk, item])
        self.choices = choices

    def filter_args(self, value):
        cvalue = self.cleaned_value(value)
        if not cvalue:
            return {}
        else:
            return {self.filter_attribute + '__pk': cvalue}

    def Q(self, value):
        return None

class BooleanModelField(BooleanColumn):
    """ Checks to see if a field has been set.  Renders as a boolean.
    Uses <attr>__isnull in filters.
    """
    def __init__(self, attr,
                 sortable=True,
                 searchable=True,
                 filter_attribute = None,
                 *args, **kwargs):
        kwargs['sortable'] = sortable
        kwargs['searchable'] = searchable
        super(BooleanModelField, self).__init__(attr, *args, **kwargs)
        self.filter_attribute = filter_attribute or self.attr

    def sort(self, direction='asc'):
        if not self.sortable:
            return None
        name = self.filter_attribute
        if direction == 'desc':
            name = '-'+name
        return name

    def filter_args(self, value):
        cvalue = self.cleaned_value(value)
        if cvalue is None:
            return {}
        else:
            return {self.filter_attribute + '__isnull': not bool(cvalue)}

class ManyToManyManagerField(ModelTableColumn):
    DEFAULT_RENDERER = ManyToManyManagerRenderer()
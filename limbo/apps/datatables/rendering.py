import datetime
import traceback
from django.utils.datastructures import SortedDict
from django.template import defaultfilters
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
from limbo import forms
from limbo.apps.datatables.util import get_attr, test_rights
import logging

log = logging.getLogger(__file__)

__all__ = [
    'ICON', 'CENTERED_ICON', 'CellRenderer', 'LinkRenderer',
    'AbsoluteURLRenderer', 'BooleanRenderer', 'row_render_dict',
    'ManyToManyManagerRenderer',
    ]

ICON = '<span class="ui-icon %s"></span>'
CENTERED_ICON = '<div class="center">%s</div>' %ICON

class CellRenderer:
    def __init__(self):
        """ Renders a cell content for the table """

    def value(self, request, obj, path = None, form = None):
        if path is None or path in ('__str__', '__unicode__'):
            return str(obj)
        else:
            v = get_attr(request, obj, path, form)
            if v is None:
                v = '-'
            return v

    def editable(self, request, obj, path, form):
        if not form:
            return False
        v = self.value(request, obj, path, form)
        try:
            return issubclass(v.__class__, (forms.Widget, forms.BoundField))
        except:
            log.error(traceback.format_exc())
            return False

    def render(self, request, obj, path = None, form = None):
        value = self.value(request, obj, path, form)
        try:
            if isinstance(value, (datetime.datetime, datetime.date)):
                return defaultfilters.date(value)
            elif isinstance(value, datetime.time):
                return defaultfilters.time(value)
            else:
                return smart_unicode(value)
        except Exception:
            log.error(traceback.format_exc())
            return str(value)

    def render_from_string(self, request, obj, s):
        return s

class LinkRenderer(CellRenderer):
    def __init__(self, link_path, request_test = None, permission = None):
        """ Renders a cell content for the table """
        self.link_path = link_path
        self.permission = permission
        self.request_test = request_test
        CellRenderer.__init__(self)

    def render(self, request, obj, path = None, form = None):
        s = CellRenderer.render(self, request, obj, path)
        if test_rights(request, self.request_test, self.permission):
            return self.render_from_string(request, obj, s)
        else:
            return s

    def render_from_string(self, request, obj, s):
        link = get_attr(request, obj, self.link_path)
        if not link:
            return s
        return "<a href='%s'>%s</a>" %(link, s)

class AbsoluteURLRenderer(LinkRenderer):
    def __init__(self, *args, **kwargs):
        LinkRenderer.__init__(self, 'get_absolute_url', *args, **kwargs)

def row_render_dict(renderer = AbsoluteURLRenderer()):
    d = SortedDict()
    d['__row__'] = renderer
    return d

class BooleanRenderer(CellRenderer):
    def render(self, request, obj, path = None, form = None):
        if self.editable(request, obj, path, form):
            return CellRenderer.render(self, request, obj, path, form)
        value = self.value(request, obj, path, form)
        return self.render_bool(value, True)

    @classmethod
    def render_bool(cls, value, centered = False):
        s = centered and CENTERED_ICON or ICON
        if isinstance(value, basestring):
            if value.lower().startswith('t') or str(value) == '1':
                value = True
            else:
                value = False
        if value:
            return mark_safe(s % 'ui-icon-check')
        else:
            return mark_safe(s% 'ui-icon-closethick')

class ManyToManyManagerRenderer(CellRenderer):

    def render(self, request, obj, path = None, form = None):
        value = self.value(request, obj, path, form)
        try:
            s = ', '.join([str(item) for item in value.all()[:5]])
            if value.all().count() > 5:
                s += ' ...'
            return s
        except Exception:
            log.error(traceback.format_exc())
            return str(value)
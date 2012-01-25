from copy import deepcopy
import traceback
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.encoding import StrAndUnicode
from django.db.models import Q
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
from django.utils import simplejson
from django.utils.datastructures import SortedDict
from django.views.generic.simple import direct_to_template
from django.utils.html import conditional_escape
from django import template
import logging
from limbo.ajax import AjaxMessage, json_response
from limbo.apps.datatables.fields import TableField
from limbo.meta import DeclarativeFieldsMetaclass
from limbo.strings import unslugify

logger = logging.getLogger(__file__)

DEFAULT_TEMPLATE = 'datatables/stub.server_data_table.html'
DEFAULT_STATIC_TEMPLATE = 'datatables/stub.static_data_table.html'
DEFAULT_BASE = 'datatables/generic_table_base.html'

class BoundColumn:
    def __init__(self, label, column, key = None, ):
        self.column = deepcopy(column)
        self.column.label = label
        self.label = label
        self.key = key

    @property
    def attr(self):
        return self.column.attr

    @property
    def visible(self):
        return self.column.visible

    @property
    def sortable(self):
        return self.column.sortable

    @property
    def searchable(self):
        return self.column.searchable

    def properties(self):
        return self.column.properties()

    def classes(self):
        return self.column.classes()

    def widget(self):
        return self.column.widget()

class DataTablesBase(StrAndUnicode):
    """ This class can be created by middleware or on the fly.

    Columns: set the declared TableColumn attributes
    Ordering: To order your queryset call the DataTables.order(queryset)
    Filtering: To filter your queryset call the DataTables.filter(queryset)
    """
    form = None

    def __init__(self, request, form = None):
        self.request = request
        self.post = request.method == 'POST' and request.POST or None
        self.parse(request.REQUEST)
        self.columns = deepcopy(self.base_fields)
        if not self.columns:
            raise ImproperlyConfigured("You must have columns in your table.")
        if form: # You could have set a default form for the any table.
            self.form = form
        super(DataTablesBase, self).__init__()

    def parse(self, data):
        self.clean_data(data)
        # Get the number of columns
        self.cols = self._get_int('iColumns',0)
        #Safety measure. If someone messes with iDisplayLength manually, we clip it to the max value of 100.
        self.iDisplayLength =  min(self._get_int('iDisplayLength',10),100)
        self.length = self.iDisplayLength

        # Where the data starts from (page)
        self.startRecord = self._get_int('iDisplayStart',0)
        # where the data ends (end of page)
        self.endRecord = self.startRecord + self.length

    def clean_data(self, data):
        self.raw_data = data
        cleaned = SortedDict()
        for key, value in data.items():
            cleaned[key] = conditional_escape(value)
        self.data = cleaned

    def keys(self):
        return self.columns.keys()

    def values(self):
        return self.columns.values()

    def items(self):
        return self.columns.items()

    @property
    def sColumns(self):
        # Pass sColumns
        return ",".join(map(str, self.column_names))

    @property
    def column_names(self):
    #        return [column.name for column in self.values()]
        return self.column_labels

    @property
    def column_labels(self):
        return self.labels.values()

    @property
    def labels(self):
        names = SortedDict()
        for key, column in self.items():
            if column.label:
                names[key] = column.label
            else:
                names[key] = unslugify(key).title()
        return names

    @property
    def column_attrs(self):
        return self.values()

    def sort(self, queryset):
        # Ordering data
        iSortingCols =  self._get_int('iSortingCols',0)
        asortingCols = []
        sortableColumns = self.sortable_columns
        if not sortableColumns:
            return queryset

        if iSortingCols:
            columns = self.columns.values()
            for sortedColIndex in range(0, iSortingCols):
                sortedColID = self._get_int('iSortCol_'+str(sortedColIndex),0)
                if self.data.get('bSortable_%s' % sortedColID, 'false')  == 'true':  # make sure the column is sortable first
                    try:
                        column = columns[sortedColID]
                    except IndexError:
                        continue
                    sortingDirection = self.data.get('sSortDir_'+str(sortedColIndex), 'asc')
                    sortedColName = column.sort(sortingDirection)
                    if sortedColName:
                        asortingCols.append(sortedColName)
            if asortingCols:
                queryset = queryset.order_by(*asortingCols)
        return queryset

    def filter(self, queryset):
        searchableColumns = self.searchable_columns
        # Apply filtering by value sent by user
        customSearch = self.data.get('sSearch', '').encode('utf-8').split(' ')
        for customSearchStr in customSearch:
            if customSearchStr != '':
                outputQ = None
                for searchableColumn in searchableColumns:
                    q = searchableColumn.Q(customSearchStr)
                    if q:
                        outputQ = outputQ | q if outputQ else q
                queryset = queryset.filter(outputQ)

        # Individual column search
        for col in range(0, self.cols):
            if self.data.get('sSearch_%s' %col, False) > '' and self.data.get('bSearchable_%s' %col, False) == 'true':
                column = self.values()[col]
                if column.searchable:
                    value = self.data['sSearch_%s' %col]
                    queryset = column.filter_queryset(queryset, value)
        return queryset

    @property
    def searchable_columns(self):
        return [column for column in self.values() if column.searchable]

    @property
    def sortable_columns(self):
        return [column for column in self.values() if column.sortable]

    def _get_int(self, key, default=0):
        try:
            return int(self.data.get(key, default))
        except ValueError:
            return default

    def make_form(self, obj):
        return self.form(data = self.post, instance = obj,
            prefix="%s_%s" %(slugify(obj.__class__.__name__), obj.pk))

    def row_data(self, obj):
        row = []
        if self.form:
            form = self.make_form(obj)
        else:
            form = None
        for col in self.columns.values():
            row.append(col.render(self.request, obj, col.attr, form))
        return row

    def sub_queryset(self, queryset, filter = True):
        queryset = self.sort(queryset)
        if filter:
            queryset = self.filter(queryset)

        #get the slice
        queryset = queryset[self.startRecord:self.endRecord]
        return queryset

    @property
    def editable(self):
        return bool(self.form)

    def save(self, queryset, *args, **kwargs):
        response_dict = {}
        subset = self.sub_queryset(queryset)

        all_valid = True
        errors = {}
        for item in subset:
            form = self.make_form(item)
            if form.is_bound and form.is_valid():
                form.save()
            else:
                all_valid = False
                errors.update(form.errors)
        response_dict['success'] = all_valid
        if all_valid:
            response_dict['message'] = AjaxMessage("Table Data Saved", AjaxMessage.SUCCESS)
        response_dict['errors'] = errors
        response =  HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')
        add_never_cache_headers(response)
        return response

    def rows(self, queryset):
        rows = []
        for obj in queryset:
            rows.append(self.row_data(obj))
        return rows

    def response(self, queryset, jsonTemplatePath = None, *args):
        queryset = self.filter(queryset)

        #count how many records match the final criteria
        iTotalRecords = iTotalDisplayRecords = queryset.count()

        queryset = self.sub_queryset(queryset, False)
        # required echo response
        sEcho = self._get_int('sEcho',0)
        if jsonTemplatePath:
            #prepare the JSON with the response, consider using : from django.template.defaultfilters import escapejs
            jstonString = render_to_string(jsonTemplatePath, locals())
            response = HttpResponse(jstonString, mimetype="application/javascript")
        else:
            aaData = self.rows(queryset)
            response_dict = {}
            response_dict.update({'aaData':aaData})
            response_dict.update({'sEcho': sEcho, 'iTotalRecords': iTotalRecords, 'iTotalDisplayRecords':iTotalDisplayRecords, 'sColumns':self.sColumns})
            response =  json_response(response_dict)
        add_never_cache_headers(response)
        return response

    def display(self):
        d = []
        labels = self.labels
        for key, label in labels.items():
            d.append(BoundColumn(label, self.columns[key], key))
        return d

    def __iter__(self):
        return self.display().__iter__()

class DataTable(DataTablesBase):
    __metaclass__ = DeclarativeFieldsMetaclass

    class Meta:
        declaritive_types = {
            "base_fields": TableField,
            }

class ModelDataTableBase(DataTablesBase):
    """ A data table representation that knows how to render itself """
    DEFAULT_TEMPLATE = DEFAULT_TEMPLATE
    DEFAULT_STATIC_TEMPLATE = DEFAULT_STATIC_TEMPLATE
    DEFAULT_BASE = DEFAULT_BASE

    # Extended initialization of the data table
    id='server_table'
    base=DEFAULT_BASE
    server_template=DEFAULT_TEMPLATE
    static_template=DEFAULT_STATIC_TEMPLATE
    form=None
    title=None
    search_form=None
    add_path=None
    jsonTemplatePath=None
    source_path=None

    def __init__(self, request, source_url = None, title=None):
        self.base = DEFAULT_BASE
        self.source = source_url or request.path
        DataTablesBase.__init__(self, request)
        self.title = title or self.title

    def save(self, queryset, *args, **kwargs):
        return DataTablesBase.save(self, queryset,
            *args, **kwargs)

    def render(self, request, context, template = 'datatables/server_data_table.html'):
        context['table'] = self
        template = self.template or template
        return direct_to_template(request, template, context, )

    @property
    def template(self):
        template = getattr(self, '_template', None)
        if template:
            return template
        if self.is_static():
            return self.static_template
        else:
            return self.server_template

    @template.setter
    def template(self, template):
        self._template = template

    @classmethod
    def make(cls, request, *args, **kwargs):
        if cls.source_path:
            url = reverse(cls.source_path, args = args, kwargs = kwargs)
        else:
            url = None
        tbl = cls(request, url)
        if tbl.is_static() and tbl.template == DEFAULT_TEMPLATE:
            tbl.template = DEFAULT_STATIC_TEMPLATE
        return tbl

    def is_static(self):
        return not self.source_path

    @property
    def queryset(self):
        return getattr(self, '_queryset', None)

    @queryset.setter
    def queryset(self, queryset):
        self._queryset = queryset

    def rows(self, queryset=None):
        if queryset is None:
            queryset = self.queryset
        return super(ModelDataTableBase, self).rows(queryset)

    def add_url(self, *args, **kwargs):
        if not self.add_path:
            return ''
        try:
            return reverse(self.add_path, args=args, kwargs=kwargs)
        except:
            logger.error(traceback.format_exc())
            return ''

    def __unicode__(self):
        dictionary = {
            'table':self,
            }
        return render_to_string(self.template, dictionary, template.Context(dictionary))

class ModelDataTable(ModelDataTableBase):
    __metaclass__ = DeclarativeFieldsMetaclass

    class Meta:
        declaritive_types = {
            "base_fields": TableField,
            }

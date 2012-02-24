from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateView
from django.views.generic.list import ListView
from limbo.context import PageContext


class GenericDatatableAjaxView(ListView):
    datatable = None
    response_type='json'
    is_ajax=True
    template_name='datatables/server_data_table.html'
    queryset_func = None

    def __init__(self, datatable=None, queryset_func=None):
        super(GenericDatatableAjaxView, self).__init__()
        self.datatable = datatable or self.datatable
        self.queryset_func = queryset_func or self.queryset_func

    def get_queryset(self):
        if self.queryset_func:
            return self.queryset_func(self)
        return super(GenericDatatableAjaxView, self).get_queryset()

    def make_datatable(self, **kwargs):
        return self.datatable.make(self.request)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        return self.make_datatable(**kwargs).response(queryset)

class DatatablesView(TemplateView):
    datatable = None
    datatable_view_class = GenericDatatableAjaxView
    context_class = PageContext
    template_name = 'datatables/server_data_table.html'

    def make_datatable(self, **kwargs):
        return self.datatable.make(self.request)

    def get_context_data(self, **kwargs):
        context = super(DatatablesView, self).get_context_data(**kwargs)
        table = self.make_datatable(**kwargs)
        context['table'] = table
        return context

    @classmethod
    def get_queryset_func(cls):
        """
        This returns a callable that will take in the ajax view as it's only argument.
        You will have access to the request via view.request, and all other class
        objects the same way.
        """
        return None

    @classmethod
    def table_initkwargs(cls, **kwargs):
        kwargs['datatable'] = cls.datatable
        kwargs['queryset_func'] = cls.get_queryset_func()
        return kwargs


    @classmethod
    def table_view(cls, **kwargs):
        return cls.datatable_view_class.as_view(**cls.table_initkwargs(**kwargs))

from django.http import Http404
from django.views.generic.base import View, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from limbo.apps.datatables.views import DatatablesView, GenericDatatableAjaxView

__author__ = 'gdoermann'

class ProtectedMixin(object):
    permissions = tuple()
    request_tests = tuple()
    decorators = tuple()

    def protect(self, request, *args, **kwargs):
        for perm in self.permissions:
            if not request.user.has_perm(perm):
                raise Http404()

    def do_dispatch(self, dispatcher, request, *args, **kwargs):
        self.protect(request, *args, **kwargs)
        def do_dispatch(*nargs, **nkwargs):
            return dispatcher(request, *args, **kwargs)
        f = do_dispatch
        for deco in self.decorators:
            f = deco(f)
        return f(request, *args, **kwargs)

class ProtectedDetailView(ProtectedMixin, DetailView):
    def dispatch(self, request, *args, **kwargs):
        return self.do_dispatch(super(ProtectedDetailView, self).dispatch,
            request, *args, **kwargs)

class ProtectedTemplateView(ProtectedMixin, TemplateView):
    def dispatch(self, request, *args, **kwargs):
        return self.do_dispatch(super(ProtectedTemplateView, self).dispatch,
            request, *args, **kwargs)

class ProtectedCreateView(ProtectedMixin, CreateView):
    def dispatch(self, request, *args, **kwargs):
        return self.do_dispatch(super(ProtectedCreateView, self).dispatch,
            request, *args, **kwargs)

class ProtectedUpdateView(ProtectedMixin, UpdateView):
    def dispatch(self, request, *args, **kwargs):
        return self.do_dispatch(super(ProtectedUpdateView, self).dispatch,
            request, *args, **kwargs)

class ProtectedDatatableAjaxView(ProtectedMixin, GenericDatatableAjaxView):
    def __init__(self, **kwargs):
        """
        Permissions are shared across the datatable and ajax views.
        """
        self.permissions = kwargs.pop('permissions') or self.permissions
        self.request_tests = kwargs.pop('request_tests') or self.request_tests
        self.decorators = kwargs.pop('decorators') or self.decorators
        self.model = kwargs.pop('model') or self.model
        super(ProtectedDatatableAjaxView, self).__init__(**kwargs)


class ProtectedDatatablesView(ProtectedMixin, DatatablesView):
    datatable_view_class = ProtectedDatatableAjaxView
    model = None

    def dispatch(self, request, *args, **kwargs):
        return self.do_dispatch(super(ProtectedDatatablesView, self).dispatch,
            request, *args, **kwargs)

    @classmethod
    def table_initkwargs(cls, **kwargs):
        kwargs = super(ProtectedDatatablesView, cls).table_initkwargs(**kwargs)
        kwargs['permissions'] = cls.permissions
        kwargs['request_tests'] = cls.request_tests
        kwargs['decorators'] = cls.decorators
        kwargs['model'] = cls.model
        return kwargs


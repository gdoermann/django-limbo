import os
from django.contrib import messages
import traceback
from django.contrib.auth.views import login
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.utils.importlib import import_module
from limbo import exceptions
from django.views.static import serve
from limbo.paths import request_full_url
from limbo.strings import unslugify
from django.utils.translation import ugettext as _
from django.core.urlresolvers import Resolver404, reverse
import logging
from django.conf import settings
urlconf = settings.ROOT_URLCONF
urls = import_module(settings.ROOT_URLCONF)

log = logging.getLogger(__file__)

class LoginMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if any([
                view_kwargs.pop('public', False),
                request.user.is_authenticated(),
                view_func == serve,
                view_func == login,
                request.path.startswith(settings.MEDIA_URL),
                os.path.splitext(request.path)[-1].lower() in ('.ico', '.png', '.jpg', '.gif')
                ]):
            return
        if request.method == 'POST':
            response = login(request)
            if request.user.is_authenticated():
                return HttpResponseRedirect(request.path)
            return response
        else:
            return login(request)

class ExceptionsMiddleware(object):
    def process_exception(self, request, exception):
        if isinstance(exception, exceptions.ReloadRequest):
            exception.path = request_full_url(request)
            return exception.response
        elif isinstance(exception, exceptions.SecurityError):
            messages.debug(request, traceback.format_exc())
            exception.log(request)
            new_e = exceptions.RedirectRequest('/')
            return new_e.response
            # TODO: Redirect to a 403 forbidden page with full content
        elif isinstance(exception, exceptions.MiddlewareException) and \
             'response' in dir(exception):
            return exception.response

class PaginationMiddleware(object):
    def process_request(self, request):
        try:
            request.paginate_by = min(int(request.GET.get('paginate_by', 100)), 100)
        except ValueError:
            request.paginate_by = 100

class RequestMiddleware:
    def process_request(self, request):
        """
        Puts is_post, is_get, post_data, get_data and file_data on the request object
        """
        request.is_get = self.is_get(request)
        request.is_post = self.is_post(request)
        request.post_data = self.post_data(request)
        request.get_data = self.get_data(request)
        request.file_data = self.file_data(request)
        request.urls = self.default_urls()

        def post_data_prefix(prefix):
            data = request.post_data
            if not data:
                return None
            for key in data.keys():
                if key.startswith(prefix):
                    return data

        request.post_data_prefix = post_data_prefix


    def is_post(self, request):
        return request.method in ('POST', 'PUT')

    def is_get(self, request):
        return request.method == 'GET'


    def post_data(self, request, key = None):
        """ Returns the POST dictionary object if the request is of method POST, else None """
        if self.is_post(request):
            if not key:
                return request.POST
            else:
                if request.POST.has_key(key):
                    return request.POST
        return None

    def file_data(self, request):
        """ If request is of method POST, returns request.FILES """
        if self.is_post(request):
            return request.FILES
        return None

    def get_data(self, request):
        if self.is_get(request) and len(request.GET.keys()) > 0:
            return request.GET
        return None

    def default_urls(self):
        urls = {
            "random_string":reverse('limbo:random_string'),
            "message_sync":reverse('limbo:message_sync'),
            "js_errors":reverse('limbo:js_errors'),
        }

        return urls

class Pages:
    def __init__(self, request, view_func, view_args, view_kwargs):
        self.request = request
        self.view_func = view_func
        self.view_args = view_args
        self.view_kwargs = view_kwargs
        if self.is_static_media():
            return
        self.parse_page()
        self.parse_breadcrumbs()
        request.relative_path = self.relative_path

    def relative_path(self, offset = 0):
        offset = abs(offset)
        path = self.request.path
        ews = path.endswith('/')
        if ews:
            path = path[:-1]
        parts = path.split('/')
        if len(parts) < offset:
            return '/'
        rpath = parts[:-offset]
        if ews:
            rpath += ['']
        return '/'.join(rpath)


    def is_static_media(self):
        media_root = settings.MEDIA_ROOT[1:]
        path = self.request.path[1:]
        return path.startswith(media_root)

    def parse_breadcrumbs(self):
        if not hasattr(self.request, 'breadcrumbs'):
            return
        self.parse_display()
        history = []
        for part in self.request.path.split('/'):
            if not part:
                continue
            history.append(part)
            url = '/'.join(history + [""])
            for pattern in urls.urlpatterns:
                try:
                    resolved = pattern.resolve(url)
                    if resolved:
                        view, arts, kwargs = resolved
                        display = kwargs.get('dislpay', self.get_url_display(url, kwargs))
                        self.request.breadcrumbs(_(display), '/' + url)
                except Resolver404:
                    pass
                except Exception:
                    log.error(traceback.format_exc())

    def parse_page(self):
        self.page = self.view_kwargs.pop('page', None)
        
    def parse_display(self):
        self.display = self.view_kwargs.pop('display', self.get_url_display())

    def get_url_display(self, path = None, kwargs = None):
        if path is None:
            path = self.request.path
        if kwargs is None:
            kwargs = self.view_kwargs
        parts = path.split('/')
        try:
            new_path = parts[-1]
            if not new_path:
                new_path = parts[-2]
            return unslugify(new_path).title()
        except IndexError:
            return ""

class PageMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        request.pages = Pages(request, view_func, view_args, view_kwargs)

try:
    from debug_toolbar.middleware import DebugToolbarMiddleware
except:
    DebugToolbarMiddleware = object

class AdminDebugToolbarMiddleware(DebugToolbarMiddleware):
    """ All superusers see debug toolbar """
    def _show_toolbar(self, request):
        if request.user.is_superuser:
            return True
        else:
            return super(AdminDebugToolbarMiddleware, self)._show_toolbar(request)

from limbo.dashboards import DashboardForm
from django.utils.translation import ugettext as _
from django.template import RequestContext
from limbo import forms
from django import template
from limbo.ajax import json
from django.conf import settings

class PageContext(dict):
    """
    Helper objects.  Really just a dictionary with certain properties that are required.

    Default Properties:
        PAGE: can be used for deciding which overall tab/ app you are on.
        title: usually the title of the html page
        urls: any urls you want to add to the page.  This are nice so you can determine urls and then pass it down for
                future use in javascript.  This is used in the Limbo ajax framework.
    """
    def __init__(self, request, title, page = None, d = dict()):
        super(PageContext, self).__init__()
        self.title = title
        if page:
            self['PAGE'] = page
        self.update(d)
        self.request = request
        if hasattr(request, 'breadcrumbs') and title:
            bd_title = title.split(':')[-1].strip()
            request.breadcrumbs(_(bd_title), request.path)

    def _set_urls(self, urls):
        self['urls'] = urls
    def _get_urls(self):
        if not self.has_key('urls'):
            self.urls = {}
        return self.get('urls')
    urls = property(_get_urls, _set_urls)

    def _set_title(self, title):
        self['title'] = title
    def _get_title(self):
        return self['title']
    title = property(_get_title, _set_title)

    @property
    def request_context(self):
        return RequestContext(self.request, self)

class FormContext(PageContext):
    """ This is used for setting up a page with a default form.  This will set the different variables used for
        creating up the form so you can use default templates, and still get custom form actions.
        Many generic form templates in limbo work with this structure.
        Additional Properties:
            form: the default django form object you want to display
            cancel_url: the url to go to if the user hit's cancel
            header: the form header
            method: the form submit method (default=post)
            action: the action to perform on submit
    """
    def __init__(self, request, title, page = None, d = dict(), action = None, method='post', header = None, cancel_url = None, classes = list()):
        super(FormContext, self).__init__(request, title, page, d)
        self.cancel_url = cancel_url
        self.header = header
        self.method = method
        self.action = action
        self.classes = classes

    def _set_form(self, form):
        self['form'] = form
    def _get_form(self):
        return self.get('form', None)
    form = property(_get_form, _set_form)

    def _set_header(self, value):
        if value:
            self['form_header'] = value
    def _get_header(self):
        return self.get('form_header', None)
    header = property(_get_header, _set_header)

    def _set_cancel_url(self, value):
        if value:
            self['cancel_url'] = value
    def _get_cancel_url(self):
        return self.get('cancel_url', None)
    cancel_url = property(_get_cancel_url, _set_cancel_url)

    def _set_method(self, value):
        if value:
            self['form_method'] = value
    def _get_method(self):
        return self.get('form_method', None)
    method = property(_get_method, _set_method)

    def _set_action(self, value):
        if value:
            self['form_action'] = value
    def _get_action(self):
        return self.get('form_action', None)
    action = property(_get_action, _set_action)

    def _set_classes(self, value):
        if value:
            self['form_classes'] = value
    def _get_classes(self):
        return self.get('form_classes', None)
    classes = property(_get_classes, _set_classes)

def dashboard_context(request):
    form = DashboardForm()
    t = template.loader.get_template('dashboards/filter.html')
    c = template.Context(locals())
    return {
        'dashboard_filter_form':json.dumps(t.render(c)),
    }

def page_context(request):
    gdict = {}
    gdict.update(request.GET)
    return {
        "PAGE":hasattr(request, 'pages') and hasattr(request.pages, 'page') and request.pages.page or None,
        'URLS':request.urls,
        'SETTINGS':settings,
        'GET_DATA':json.dumps(gdict)
    }

def request_context(request):
    return {'request':request}
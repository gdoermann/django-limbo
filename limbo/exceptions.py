import csv
from django.shortcuts import render_to_response
from django.utils.datastructures import SortedDict
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
import datetime
import urllib

class FileImportError(ValueError):
    tag = "ImportErrors"
    def __init__(self, line, errors, fieldnames = [], *args, **kwargs):
        self.line = line
        self.errors = errors
        self.fieldnames = fieldnames
        self.tag = kwargs.get('tag', self.tag)
        super(FileImportError, self).__init__(self.get_message(), *args, **kwargs)

    def get_message(self):
        msg = 'Line %d has invalid data%s<br/>' % \
                (self.line, self.error_string)
        msg += 'AVAILABLE FIELDS | %r<br/>' % self.fieldnames
        return msg

    @property
    def error_string(self):
        error = [''] + [': '.join([x, ' '.join(self.errors[x])]) \
                for x in self.errors]
        return '|'.join(error)

    @property
    def xml(self):
        from xml.etree.ElementTree import Element
        e = Element("ImportError")
        lnode = Element("Line")
        lnode.text = self.line
        e.append(lnode)
        
        ie = Element("ImportError")
        for key, value in self.errors.items():
            node = Element(key)
            if isinstance(value, list):
                value = '|'.join(value)
            node.text = value
            ie.append(node)
        e.append(ie)

        available = Element("AvailableFields")
        for field in self.fieldnames:
            attrib = SortedDict()
            attrib['name'] = field
            node = Element("Field", attrib=attrib)
            available.append(node)
        e.append(available)
        return e

class MiddlewareException(Exception):
    """ A base class for middleware handled exceptions """

class SecurityError(MiddlewareException):
    """ When thrown it will log an error on the user's side and return a 403 forbidden.
    Required: Exception Middleware
    """
    def __init__(self, msg, *args, **kwargs):
        super(SecurityError, self).__init__(*args, **kwargs)
        self.msg = msg

    def log(self, request, logger = messages.error, fail_silently = False):
        logger(request, self.msg)

class RedirectRequest(MiddlewareException):
    """ Performs a redirect to the url specified.
    @param path: the url to go to
    @param data: a dictionary of get data to pass into the url
    Required: Exception Middleware
    """
    def __init__(self, path, data = None, *args, **kwargs):
        super(RedirectRequest, self).__init__(*args, **kwargs)
        self.path = path
        self.data = data

    @property
    def response(self):
        if isinstance(self.path, HttpResponse):
            return self.path
        else:
            path = self.path
            if self.data:
                if hasattr(self.data, 'urlencode'):
                    path += '?' + self.data.urlencode()
                else:
                    path += '?' + urllib.urlencode(self.data, True)
            return HttpResponseRedirect(path)

class ReloadRequest(RedirectRequest):
    """ Perform a reload of the current url.
    Figuring out the url is handled in the middleware
    Required: Exception Middleware
    """
    def __init__(self, *args, **kwargs):
        super(ReloadRequest, self).__init__(None, *args, **kwargs)

class DirectResponse(MiddlewareException):
    """
    Returns the given response without question or further processing.
    """
    def __init__(self, response, *args, **kwargs):
        super(DirectResponse, self).__init__(*args, **kwargs)
        self.response = response

class DirectTemplateResponse(MiddlewareException):
    """
    Generates a response from a template.  Overrides the current view.
    """
    def __init__(self, template_name, dictionary=None, context_instance=None,
                 mimetype=None, *args, **kwargs):
        super(DirectTemplateResponse, self).__init__(*args, **kwargs)
        self.template_name = template_name
        self.dictionary = dictionary
        self.context_instance = context_instance
        self.mimetype=mimetype

    @property
    def response(self):
        return render_to_response(template_name=self.template_name,
        dictionary = self.dictionary, context_instance = self.context_instance,
        mimetype=self.mimetype)

class CSVResponse(DirectTemplateResponse):
    def __init__(self, template_name, dictionary=None, context_instance=None,
                 mimetype='text/csv', filename=None, *args, **kwargs):
        super(DirectTemplateResponse, self).__init__(*args, **kwargs)
        self.template_name = template_name
        self.dictionary = dictionary
        self.context_instance = context_instance
        self.mimetype=mimetype
        self.filename = filename

    def set_disposition(self, response):
        response['Content-Disposition'] = 'attachment; filename="%s"' % self.full_filename()

    def full_filename(self):
        filename = self.filename
        if not filename:
            filename = '%s.csv' % datetime.date.today().strftime('%m-%d-%y')

        if filename[-4:] != '.csv':
            filename += '.csv'
        return filename
    
    @property
    def response(self):
        http_response = super(CSVResponse, self).response
        self.set_disposition(http_response)
        return http_response

class GenericCSVResponse(CSVResponse):
    def __init__(self, content, mimetype='text/csv',
                 filename=None, *args, **kwargs):
        super(GenericCSVResponse, self).__init__('', *args, **kwargs)
        self.content = content
        self.mimetype=mimetype
        self.filename = filename

    @property
    def response(self):
        http_response = HttpResponse(self.content, self.mimetype)
        self.set_disposition(http_response)
        return http_response

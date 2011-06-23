import logging
from django.contrib import messages
from django.core.mail import mail_managers
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.conf import settings
try:
    import json
except:
    import simplejson as json #@UnresolvedImport

log = logging.getLogger(__name__)

def json_response(d):
    """ Dumps dictionary into a json string and retuns a HttpResponse object of mimetype json """
    j = json.dumps(d)
    return HttpResponse(j, mimetype='application/json')

class AjaxMessage(dict):
    """ A message sent back over ajax to be displayed to the user as any other django message
    Message types are the same as django message codes

    Default properties:
        message: the message you are sending to the user
        message_type: The type of message to send to the user (default=INFO)
        undo url: in case you want to handle undo actions

    """
    DEBUG = messages.DEFAULT_TAGS[messages.DEBUG]
    INFO = messages.DEFAULT_TAGS[messages.INFO]
    SUCCESS = messages.DEFAULT_TAGS[messages.SUCCESS]
    WARNING = messages.DEFAULT_TAGS[messages.WARNING]
    ERROR = messages.DEFAULT_TAGS[messages.ERROR]
    
    def __init__(self, message, message_type = INFO, undo_url = None):
        super(AjaxMessage, self).__init__()
        self.message  = message
        self.message_type = message_type
        self.undo_url = undo_url
    
    def _set_message(self, message):
        self['message'] = message
    def _get_message(self):
        return self['message']
    message = property(_get_message, _set_message)
    
    def _set_message_type(self, t):
        self['type'] = t
    def _get_message_type(self):
        return self['type']
    message_type = property(_get_message_type, _set_message_type)
    
    def _set_undo_url(self, v):
        self['undo'] = v
    def _get_undo_url(self):
        return self['undo']
    undo_url = property(_get_undo_url, _set_undo_url)

class AjaxData(dict):
    """ A dictionary that knows how to convert itself into json
    All objects must be json serializable."""
    def json(self):
        jdict = {}
        for key, value in self.items():
            jdict[mark_safe(json.dumps(key))] = mark_safe(json.dumps(value));
        return jdict

from django.contrib.messages.storage.base import LEVEL_TAGS
def message_sync(request):
    """ An ajax call to pull messages from the server.  Returns a json list of ajax messages. """
    context = {}
    msgs = []
    for message in messages.get_messages(request):
        msgs.append(AjaxMessage(message.message, LEVEL_TAGS.get(message.level, '')))
    context['messages'] = msgs
    return json_response(context)

def js_errors(request):
    context = {}
    data = request.get_data
    if not data or not data.get('message', None):
        return json_response(context)
    kwargs = {
        'user':request.user,
    }
    for key in data.keys():
        kwargs[key] = data[key] # this is a nuance with request dicts
    full_message = """JS Error at %(url)s.
Line %(line)s.
Message: %(message)s.
User: %(user)s. 
Platform: %(browser_platform)s. 
Browser: %(browser_appname)s v.%(browser_appversion)s. 
Cookies enabled: %(browser_cookiesenabled)s """

    html_kwargs = {}
    html_kwargs.update(kwargs)
    txt_msg = full_message % kwargs
    log.exception(txt_msg.replace('\n', ' '))
    if not settings.DEBUG:
        mail_managers("[JS Error] %(message)s" %html_kwargs,
                      full_message % html_kwargs, fail_silently=False)
#    user_msg = "Some features may not be working correctly. Please try again later."
    if 'Explorer' in kwargs['browser_appname']:
        user_msg = "Some features may not be working correctly."\
        "Please try using <a href='http://chrome.google.com'>Google Chrome</a>."
        context['message'] = AjaxMessage(
            user_msg,
            messages.ERROR)
    return json_response(context)
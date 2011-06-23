from django.conf.urls.defaults import *

urlpatterns = patterns('limbo.views',
    url(r'^random_string/$', 'random_string', name='random_string'),
)

urlpatterns += patterns('limbo.ajax',
    url(r'^messages/$', 'message_sync', name='message_sync'),
    url(r'^js_errors/$', 'js_errors', name='js_errors'),
)

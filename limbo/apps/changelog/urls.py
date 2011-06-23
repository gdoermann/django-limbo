from django.conf.urls.defaults import *
from limbo.apps.changelog.feeds import ChangeLogFeed

urlpatterns = patterns('',
   url(r'^feed/$', ChangeLogFeed(), name='feed'),
   )

urlpatterns += patterns('limbo.apps.changelog.views',
    url(r'^$', 'changelog', name = 'changelog'),
    url(r'^change/$', 'change', name = 'change'),
    url(r'^change/(?P<slug>[-_\w]+)/$', 'changelog_entry', name='entry'),
    url(r'^add/$', 'add_change', name='add_change'),
    url(r'^(?P<version>[-\w\.]+)/$', 'changelog', name = 'version'),
    )
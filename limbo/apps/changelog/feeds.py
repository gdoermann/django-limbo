from django.contrib.syndication.views import Feed #@UnresolvedImport
from limbo.apps.changelog.models import Change

class ChangeLogFeed(Feed):
    title = "Changelog"
    link = '/changelog/'
    description = "New features and fixed bugs"
    
    def items(self):
        changes = Change.objects.all()
        if len(changes) > 15:
            changes = changes[:15]
        return changes
    
    def item_title(self, item):
        return item.title
    
    def item_description(self, item):
        return item.description

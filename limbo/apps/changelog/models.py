import traceback
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.safestring import mark_safe
from limbo.models import TrackedModel
from django.conf import settings

VERSIONS = settings.VERSIONS

class Change(TrackedModel):
    title = models.CharField(max_length=100, db_index=True)
    description = models.TextField()
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    version = models.IntegerField(max_length=10, choices = VERSIONS.CHOICES, default=VERSIONS.CURRENT.number, db_index=True)

    def short_description(self):
        if len(self.description) > 30:
            return self.description[:30]
        else:
            return self.description

    def url(self):
        return reverse('changelog:entry',
              kwargs={'slug': self.slug})

    def version_url(self):
        try:
            return reverse('changelog:version',
                  kwargs={
                        'version':self.get_version_display()
                  })
        except:
            traceback.print_exc()
            return "#"
    def get_absolute_url(self):
        return self.url()
    
    def description_html(self):
        d = self.description
        parts = d.replace('\r', '\n').split('\n')
        p = "<p>%s</p>\n"
        s = ''
        for part in parts:
            s += p % part
        return mark_safe(s)

    class Meta:
        ordering = ('-datetime_created', '-title')
    
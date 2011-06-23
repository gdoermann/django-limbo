from django.contrib import admin

from limbo.apps.changelog.models import Change

class ChangeAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_description', 'datetime_created', 'datetime_modified')
    fields = ('title', 'description', 'slug')
    prepopulated_fields = {'slug':('title',)}

admin.site.register(Change, ChangeAdmin)

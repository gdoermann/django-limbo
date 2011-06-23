from django.core.paginator import Paginator
from limbo.apps.changelog import models, forms
from django.views.generic.simple import direct_to_template
from django.utils.html import clean_html
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from limbo.context import PageContext, FormContext
from limbo.exceptions import RedirectRequest
from django.contrib import messages

def changelog(request, version = None):
    logs = models.Change.objects.all()
    title = "Changelog"
    if version:
        real_version = None
        for v in models.VERSIONS.CHOICES:
            if v[1] == version:
                logs = logs.filter(version = v[0])
                title += ': Version %s' %version
                request.breadcrumbs(title, request.path)
                real_version = v
                break
        if not real_version:
            raise RedirectRequest(reverse("changelog:changelog"))
    context = PageContext(request, title, d = locals())
    return direct_to_template(request, template='changelog/changelog.html', extra_context = context)

def change(request):
    raise RedirectRequest(reverse('changelog:changelog'))

def changelog_entry(request, slug):
    slug = clean_html(slug)
    change = get_object_or_404(models.Change, slug = slug)
    context = PageContext(request, "Change:%s" %change.title, d = locals())
    return direct_to_template(request, template = 'changelog/change.html', extra_context = context)

def add_change(request):
    form = forms.ChangeForm(request.post_data)
    if form.is_bound and form.is_valid():
        change = form.save()
        messages.success(request, "Change Created")
        raise RedirectRequest(change.get_absolute_url())
    context = FormContext(request, "Add Change", d = locals(), )
    return direct_to_template(request, template = 'forms/generic.html', extra_context=context)
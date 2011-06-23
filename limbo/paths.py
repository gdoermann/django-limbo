from urlparse import urljoin
from django.contrib.sites.models import Site

def request_full_url(request):
    try:
        return request.META.get('HTTP_REFERER', request.path)
    except KeyError:
        return request.path

def get_current_domain():
    base = Site.objects.get_current().domain
    if not base.startswith('http://'):
        base = 'http://' + base
    return base

def domain_url(*parts):
    """ Return the full domain url """
    base = get_current_domain()
    return urljoin(base, '/'.join(parts))

def full_domain_url(*parts):
    url = domain_url(*parts)
    if not url[-1] == '/':
        url += '/'
    return url

from datetime import datetime, timedelta
from limbo.exceptions import SecurityError, RedirectRequest
import logging
from django.contrib import messages

log = logging.getLogger(__file__)

class rate_limited:
    """
    Limits hit on the view to a certain number per hour on the SESSION.
    This is really a class that acts as a function!
    """
    def __init__(self, per_hour = None):
        self.per_hour = per_hour

    def __call__(self, view):
        def limited(request, *args, **kwargs):
            if not self.rate_test(view, request, self.per_hour):
                log.error('User %s over rate limit on %s' %(request.user, view))
                return self.fail(request, view)
            return view(request, *args, **kwargs)
        return limited

    def fail(self, request, view):
        raise SecurityError("You are over your limit of %s / hour on %s" %(self.per_hour, request.path))

    def rate_test(self, view, request, per_hour):
        if request.user.is_superuser:
            return True
        lviews = request.session.get('rate_limited_views', {})
        key = view.__name__
        visits = lviews.get(key, [])
        for visit in visits:
            if visit - datetime.now() > timedelta(hours=1):
                visits.remove(visit)
        log.debug('Visited %s %s times in the last hour' %(key, len(visits)))
        value = len(visits) < per_hour
        if value:
            visits.append(datetime.now())
        lviews[key] = visits
        request.session['rate_limited_views'] = lviews
        return value

class data_rate_limited(rate_limited):
    def rate_test(self, view, request, per_hour):
        if request.get_data or request.post_data:
            return rate_limited.rate_test(self, view, request, per_hour)
        return True

    def fail(self, request, view):
        messages.error(request, "You are over your limit of %s / hour on this page." %self.per_hour)
        raise RedirectRequest(request.path)

class post_rate_limited(data_rate_limited):
    def rate_test(self, view, request, per_hour):
        if request.post_data:
            return rate_limited.rate_test(self, view, request, per_hour)
        return True

class get_rate_limited(data_rate_limited):
    def rate_test(self, view, request, per_hour):
        if request.get_data:
            return rate_limited.rate_test(self, view, request, per_hour)
        return True

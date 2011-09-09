import inspect
from django.db import models
from django.db.models import Q
import datetime
from django.db.models.query import QuerySet

def optional_range(q, start = None, end = None, key = 'start_datetime'):
#        if end and datetime.datetime.now() - end < datetime.timedelta(seconds=2):
#            end = None
        filters = {}
        if start and end:
            if start == end:
                filters[key] = end
                return q.filter(**filters)
            else:
                filters[key + '__range'] = (start, end)
                return q.filter(**filters)

        if start:
            filters[key + '__gte'] = start
        if end:
            filters[key + '__lte'] = end
        if filters:
            return q.filter(**filters)
        else:
            return q

def optional_contains_range(q, start, end=None, start_key='start_datetime', end_key='end_datetime'):
#        if end and datetime.datetime.now() - end < datetime.timedelta(seconds=2):
#            end = None
        if not end:
            end = start
        q1 = q.exclude(**{end_key:None})
        q2 = q.filter(**{end_key:None})

        if start == end:
            q1_range = Q(**{start_key+'__lte':start}) | Q(**{end_key+'__gte':end})
            q1 = q1.filter(q1_range).distinct()
        else:
            q1_range = Q(**{end_key+'__lt':start}) | Q(**{start_key+'__gt':end})
            q1 = q1.exclude(q1_range).distinct()
        q2 = q2.filter(**{start_key + "__lte":end}).distinct()
        return (q1 | q2).distinct()

class TrackedModel(models.Model):
    """
    It would be nice to add some signal receivers and tack who is actually making the changes
    by processing who is logged in each time a model is changed.  It would be better to have a
    different table where a new log is added for each time the item is changed and what fields
    are changed.
    """
    datetime_created = models.DateTimeField(auto_now_add=True, default = datetime.datetime.now, db_index=True)
    datetime_modified = models.DateTimeField(auto_now=True, default = datetime.datetime.now, db_index=True)

    class Meta:
        abstract = True

class Comment(TrackedModel):
    user = models.ForeignKey('auth.User')
    comment = models.TextField()

    def __unicode__(self):
        return self.comment

    class Meta:
        ordering = ('datetime_created', )
        abstract = True

class NoteTrackedModel(TrackedModel):
    notes = models.TextField(blank=True)
    class Meta:
        abstract = True

class ActiveManager(models.Manager):
    def get_query_set(self):
        return super(ActiveManager, self).get_query_set().filter(active = True)

class ActivationModel(models.Model):
    active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    objects = models.Manager()
    actives = ActiveManager()

class CustomManager(models.Manager):
    queryset_class = QuerySet

    def get_query_set(self):
        return self.queryset_class(self.model, using=self._db)

def callable_attribute(attribute, parent=None, context = None):
    """ Tries calling the attribute as a normal method, and then as a class method """
    args = []
    kwargs = {}
    argspec = inspect.getargspec(attribute)
    func_args = argspec.args
    if func_args[0] in ['obj', ] and parent:
        args.append(parent)
    if 'context' in func_args:
        kwargs['context'] = context
    elif context:
        for key, value in context.items():
            if key in func_args:
                kwargs[key] = value
    return attribute(*args, **kwargs)

def model_attribute(model, attribute, context = None):
    """ This takes a django model and an attribute string path as
        arguments and returns the actual attribute off of the model.
        The attribute may also be a callable.
    """
    if callable(attribute):
        return callable_attribute(attribute, parent=model, context=context)
    elif not isinstance(attribute, basestring):
        return attribute
    else:
        obj = model
        for attr in attribute.split('__'):
            if callable(obj):
                obj = callable_attribute(obj, context=context)
            obj = getattr(obj, attr)
        return obj

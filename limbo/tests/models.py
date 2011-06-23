from datetime import datetime, time, timedelta
from django.forms.models import model_to_dict
from limbo import models
from limbo.testing import BaseTestCase

class LibModelUtils(BaseTestCase):
    """ You must inherit this test case and call the set_me_up on setup for it to work!
    """
    def set_me_up(self, obj, start_attr, end_attr):
        """ The model
        """
        self.defaults = model_to_dict(obj)
        model = obj.__class__
        model.objects.all().delete()
        del self.defaults[start_attr]
        del self.defaults[end_attr]
        self.model = model
        self.start_attr = start_attr
        self.end_attr = end_attr

    def test_optional_contains_range(self):
        obj = self.model( **self.defaults)

        start = datetime.combine(datetime.today(), time())
        midday = datetime.combine(datetime.today(), time(12))
        end = start + timedelta(days=1, minutes=-1)
        tomorrow = end + timedelta(days=1)
        yesterday = start - timedelta(days=1)
        hour = timedelta(hours=1)

        setattr(obj, self.start_attr, start)
        setattr(obj, self.end_attr, end)
        obj.save()

        q = self.model.objects.all()

        result = models.optional_contains_range(q, start, end, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Equals does not contain result")

        result = models.optional_contains_range(q, midday, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Right overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, midday, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Left overlap does not contain result")

        result = models.optional_contains_range(q, midday-hour, midday + hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Inside overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Outside overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, start, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Left Boundary touch does not contain result")

        result = models.optional_contains_range(q, yesterday, start+hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Left Boundary overlap does not contain result")

        result = models.optional_contains_range(q, end, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Right Boundary overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, start - hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 0, "Right non-overlap does contains result")

        result = models.optional_contains_range(q, end + hour, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 0, "Left non-overlap does contains result")

        result = models.optional_contains_range(q, midday, midday, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Equal start, end: Inside")

        result = models.optional_contains_range(q, start, start, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Equal start, end: Same as Start")

        result = models.optional_contains_range(q, end, end, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "Equal start, end: Same as End")

    def test_optional_contains_range_no_end(self):
        obj = self.model( **self.defaults)

        start = datetime.combine(datetime.today(), time())
        midday = datetime.combine(datetime.today(), time(12))
        end = start + timedelta(days=1, minutes=-1)
        tomorrow = end + timedelta(days=1)
        yesterday = start - timedelta(days=1)
        hour = timedelta(hours=1)

        setattr(obj, self.start_attr, start)
        setattr(obj, self.end_attr, end)
        obj.save()

        q = self.model.objects.all()

        result = models.optional_contains_range(q, start, end, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Equals does not contain result")

        result = models.optional_contains_range(q, midday, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Right overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, midday, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Left overlap does not contain result")

        result = models.optional_contains_range(q, midday-hour, midday + hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Inside overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Outside overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, start, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Left Boundary touch does not contain result")

        result = models.optional_contains_range(q, yesterday, start+hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Left Boundary overlap does not contain result")

        result = models.optional_contains_range(q, yesterday, start - hour, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 0, "No End: Left non-overlap does contains result")

        result = models.optional_contains_range(q, end + hour, tomorrow, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Right overlap does not contains result")

        result = models.optional_contains_range(q, midday, midday, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Equal start, end: Inside")

        result = models.optional_contains_range(q, start, start, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Equal start, end: Same as Start")

        result = models.optional_contains_range(q, end, end, self.start_attr, self.end_attr)
        self.assertEquals(result.count(), 1, "No End: Equal start, end: Same as End")


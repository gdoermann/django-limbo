from django import template
from limbo.drilldown.util import DateDrillDown

register = template.Library()

class DateDrillDownNode(DateDrillDown):
    pass

class MonthDrillDownNode(DateDrillDownNode):
    def days(self, year, month):
        return []

@register.tag
def date_drill_down(parser, token):
    try:
        items = token.split_contents()
        d = {}
        for item in items:
            d[items.index(item)] = item
        object = items[1]
        date_attr = d.get(2, None)
    except IndexError:
        raise template.TemplateSyntaxError, "%r tag must specify a an object" % token.contents.split()[0]

    return DateDrillDownNode(object, date_attr)

@register.tag
def month_drill_down(parser, token):
    try:
        items = token.split_contents()
        d = {}
        for item in items:
            d[items.index(item)] = item
        object = items[1]
        date_attr = d.get(2, None)
    except IndexError:
        raise template.TemplateSyntaxError, "%r tag must specify a an object" % token.contents.split()[0]

    return MonthDrillDownNode(object, date_attr)

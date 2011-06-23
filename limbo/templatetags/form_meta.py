from django import template

register = template.Library()

def get_id(context, field):
    form = context['form']
    return {'value': form[field].auto_id}

register.inclusion_tag("forms/value", takes_context=True)(get_id)
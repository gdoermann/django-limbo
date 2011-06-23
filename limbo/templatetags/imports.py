from django import template
from django.core.validators import EMPTY_VALUES
from limbo import forms

def get_field_type(field):
    if field.initial:
        return type(field.initial)
    elif isinstance(field, forms.IntegerField):
        return 'Integer'
    elif isinstance(field, forms.FloatField):
        return "Number"
    elif isinstance(field, forms.NullBooleanField):
        return "Boolean (Empty okay)"
    elif isinstance(field, forms.BooleanField):
        return "Boolean"
    elif isinstance(field, forms.CharField):
        return "String"

register = template.Library()
def field_instructions(context, field_name):
    form = context['form']
    context = {}
    field = form.fields[field_name]
    context['field'] = field
    context['name'] = field_name
    choices = None
    if hasattr(field, 'choices'):
        choices = list(field.choices)
        for tup in choices:
            if tup[0] in EMPTY_VALUES:
                choices.remove(tup)
    if isinstance(field, forms.NullBooleanField):
        choices = (
            ('', 'Unknown'),
            ('0', 'False'),
            ('1', 'True'),
            )
    elif isinstance(field, forms.BooleanField):
        choices = (
            ('0', 'False'),
            ('1', 'True'),
            )
    context['choices'] = choices

    context['index'] = form.fields.keys().index(field_name)+1
    constraints = {}
    if hasattr(field, 'initial') and field.initial:
        constraints['Default'] = field.initial
    if hasattr(field, 'max_length') and field.max_length:
        constraints['Max Length'] = '%i characters' % field.max_length
    if hasattr(field, 'max_value') and field.max_value:
        constraints['Max Value'] = field.max_value
    if hasattr(field, 'min_length') and field.min_length:
        constraints['Min Length'] = '%i characters' % field.min_length
    if hasattr(field, 'min_length') and field.min_length:
        constraints['Min Value'] = field.min_value
    if get_field_type(field):
        constraints['Type'] = get_field_type(field)
    context['constraints'] = constraints
    return context
register.inclusion_tag("forms/stub.import_instruction_row.html",  takes_context=True)(field_instructions)



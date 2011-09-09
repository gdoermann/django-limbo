from django.utils.datastructures import SortedDict

class DeclaredField(object):
    # Tracks each time a Field instance is created. Used to retain order.
    _creation_counter = 0

    def __init__(self, *args, **kwargs):
        # Increase the creation counter, and save our local copy.
        self._creation_counter = DeclaredField._creation_counter
        DeclaredField._creation_counter += 1

def get_declared_fields(bases, attrs, field_name = 'base_fields', field_cls = DeclaredField):
    """
    Create a list of declared field instances from the passed in 'attrs', plus any
    similar fields on the base classes (in 'bases').
    """
    fields = [(field_name, attrs.pop(field_name)) for field_name, obj in attrs.items() if isinstance(obj, field_cls)]
    fields.sort(lambda x, y: cmp(x[1]._creation_counter, y[1]._creation_counter))

    for base in bases[::-1]:
        if hasattr(base, field_name):
                fields = base.base_fields.items() + fields

    return SortedDict(fields)

class DeclarativeFieldsMetaclass(type):
    """
    Metaclass that converts Field attributes to a dictionary called
    'base_fields', taking into account parent class 'base_fields' as well.
    It will find all objects that extend DeclaredField.
    """
    def __new__(cls, name, bases, attrs):
        if attrs.has_key('Meta') and hasattr(attrs['Meta'], "declaritive_types"):
            declaritive_types = attrs['Meta'].declaritive_types
        else:
            declaritive_types = {'base_fields':DeclaredField}
        for field_name, field_cls in declaritive_types.items():
            attrs[field_name] = get_declared_fields(bases, attrs, field_name, field_cls=field_cls)
        new_class = super(DeclarativeFieldsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class


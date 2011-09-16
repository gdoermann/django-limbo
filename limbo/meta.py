from django.utils.datastructures import SortedDict

## {{{ http://code.activestate.com/recipes/204197/ (r5)
import inspect, types, __builtin__

############## preliminary: two utility functions #####################

def skip_redundant(iterable, skipset=None):
   "Redundant items are repeated items or items in the original skipset."
   if skipset is None: skipset = set()
   for item in iterable:
       if item not in skipset:
           skipset.add(item)
           yield item


def remove_redundant(metaclasses):
   skipset = set([types.ClassType])
   for meta in metaclasses: # determines the metaclasses to be skipped
       skipset.update(inspect.getmro(meta)[1:])
   return tuple(skip_redundant(metaclasses, skipset))

##################################################################
## now the core of the module: two mutually recursive functions ##
##################################################################

memoized_metaclasses_map = {}

def get_noconflict_metaclass(bases, left_metas, right_metas):
    """Not intended to be used outside of this module, unless you know
    what you are doing."""
    # make tuple of needed metaclasses in specified priority order
    metas = left_metas + tuple(map(type, bases)) + right_metas
    needed_metas = remove_redundant(metas)

    # return existing confict-solving meta, if any
    if needed_metas in memoized_metaclasses_map:
      return memoized_metaclasses_map[needed_metas]
    # nope: compute, memoize and return needed conflict-solving meta
    elif not needed_metas:         # wee, a trivial case, happy us
        meta = type
    elif len(needed_metas) == 1: # another trivial case
       meta = needed_metas[0]
    # check for recursion, can happen i.e. for Zope ExtensionClasses
    elif needed_metas == bases:
        raise TypeError("Incompatible root metatypes", needed_metas)
    else: # gotta work ...
        metaname = '_' + ''.join([m.__name__ for m in needed_metas])
        meta = classmaker()(metaname, needed_metas, {})
    memoized_metaclasses_map[needed_metas] = meta
    return meta

def classmaker(left_metas=(), right_metas=()):
   def make_class(name, bases, adict):
       metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
       return metaclass(name, bases, adict)
   return make_class
## end of http://code.activestate.com/recipes/204197/ }}}



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
        if hasattr(base, field_name) and isinstance(getattr(base, field_name), dict):
            fields = getattr(base, field_name).items() + fields

    return SortedDict(fields)

class DeclarativeFieldsMetaclass(type):
    """
    Metaclass that converts Field attributes to a dictionary called
    'base_fields', taking into account parent class 'base_fields' as well.
    It will find all objects that extend DeclaredField.
    """
    def __new__(cls, name, bases, attrs):
        meta = attrs.get('Meta')
        if meta and hasattr(meta, "declaritive_types"):
            declaritive_types = meta.declaritive_types
        else:
            declaritive_types = {'base_fields':DeclaredField}

        for base in bases:
            if hasattr(base, 'Meta'):
                base_meta = getattr(base, 'Meta')
                if not meta:
                    meta = base_meta
                for attr in dir(base_meta):
                    if attr.startswith('_') or attr == 'declaritive_types':
                        continue
                    if not hasattr(meta, attr):
                        setattr(meta, attr, getattr(base_meta, attr))

        for field_name, field_cls in declaritive_types.items():
            attrs[field_name] = get_declared_fields(bases, attrs, field_name, field_cls=field_cls)
        new_class = super(DeclarativeFieldsMetaclass,
                     cls).__new__(cls, name, bases, attrs)
        return new_class


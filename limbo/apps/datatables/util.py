from django.core.exceptions import ObjectDoesNotExist

def get_display(request, obj, attr):
    if hasattr(obj, 'get_%s_display' %attr):
        return get_attr(request, obj, 'get_%s_display' %attr)

def get_attr(request, obj, path, form = None):
    """
    if the path is callable, it will return the callable
    passing in the object and form.
    
    Will get the attribute from the form fields
    if the attribute name is on the form, otherwise
    it will get if off the object.
    """
    if callable(path):
        return path(request, obj, form)
    obj_attr = obj
    parts = path.split('__')

    if form and form.fields.has_key(path):
        return form[path]

    # Get display
    if len(parts) == 1 and get_display(request, obj, path):
        return get_display(request, obj, path)
    part = None
    for part in parts:
        if obj_attr is None:
            return None
        try:
            obj_attr = getattr(obj_attr, part)
            if callable(obj_attr):
                obj_attr = obj_attr()
        except ObjectDoesNotExist:
            return None
    if part and get_display(request, part, parts[-1]):
        return get_display(request, part, parts[-1])
    return obj_attr

def test_rights(request, test = None, perm = None):
    """ This cannot be simplified into a one liner... """
    try:
        has_perm = True
        if test:
            has_perm = has_perm and test(request)
        if perm:
            has_perm = has_perm and request.user.has_perm(perm)
        return has_perm
    except ObjectDoesNotExist: # Like they don't have a profile
        return False

from limbo.ajax import json_response
from limbo.strings import unique_string

def random_string(request):
    count = request.GET.get('count', 1)
    try:
        max_length = int(request.GET.get('max_length', None))
    except:
        max_length = None
    ul = {}
    for c in range(count):
        s = unique_string()
        if max_length and len(s) > max_length:
            s = s[:max_length]
        ul[c] = s
    return json_response(ul)
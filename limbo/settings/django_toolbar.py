from settings import MIDDLEWARE_CLASSES, INSTALLED_APPS

def combine_tuples(*args):
    c = []
    for l in args:
        c += list(l)
    return tuple(c)

def add_to_tuple(tup, item):
    return tuple(list(tup) + [item])

MIDDLEWARE_CLASSES = add_to_tuple(MIDDLEWARE_CLASSES, 'debug_toolbar.middleware.DebugToolbarMiddleware')

INSTALLED_APPS = add_to_tuple(INSTALLED_APPS, 'debug_toolbar')

def add_network(*interfaces):
    try:
        from settings import INTERNAL_IPS as internal_ips
    except ImportError:
        internal_ips = ('127.0.0.1',)
    try:
        from limbo.ip_address import get_ip_address
        for iface in interfaces:
            internal_ips = add_to_tuple(internal_ips, '.'.join(get_ip_address(iface).split('.')[:-1]) + '.0/24')
    except Exception:
        import traceback
        traceback.print_exc()
    return internal_ips
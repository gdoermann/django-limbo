import os
module = os.environ.get('DJANGO_SETTINGS_MODULE', 'settings')
exec('import %s as module' % module)
MIDDLEWARE_CLASSES, INSTALLED_APPS = module.MIDDLEWARE_CLASSES, module.INSTALLED_APPS

MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + ('limbo.middleware.AdminDebugToolbarMiddleware', )

INSTALLED_APPS = INSTALLED_APPS + ('debug_toolbar', )

def add_network(*interfaces):
    try:
        from settings import INTERNAL_IPS as internal_ips
        if not internal_ips:
            internal_ips = ()
    except ImportError:
        internal_ips = ('127.0.0.1',)
    try:
        from limbo.ip_address import get_ip_address
        for iface in interfaces:
            internal_ips = internal_ips + ('.'.join(get_ip_address(iface).split('.')[:-1]) + '.0/24', )
    except Exception:
        import traceback
        traceback.print_exc()
    return internal_ips
import os
__author__ = 'gdoermann'
def check_django_environment(default_settings):
    # Environment setup for Django project files:
    os.sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not os.environ.get('DJANGO_SETTINGS_MODULE'):
        # Don't override settings if it is specified.
        os.environ['DJANGO_SETTINGS_MODULE'] = default_settings
        from django.conf import settings

def check_amqp_environment(logfile, default_settings):
    os.environ['LIMBO_LOG_FILE'] = logfile
    check_django_environment(default_settings)

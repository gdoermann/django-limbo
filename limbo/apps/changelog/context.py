from django.conf import settings

def version(request):
    return {
        "CURRENT_VERSION":settings.VERSIONS.CURRENT_DISPLAY,
    }
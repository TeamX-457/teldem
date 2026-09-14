from django.conf import settings


def site_meta(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "SITE_DOMAIN": settings.SITE_DOMAIN,
        "TELDEM_BRAND": settings.TELDEM_BRAND,
    }

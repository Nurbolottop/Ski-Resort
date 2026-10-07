from django.conf import settings

from apps.base.models import SiteSettings


def site(request):
    return {'site': SiteSettings.load(), 'asset_version': settings.ASSET_VERSION}

from apps.base.models import SiteSettings


def site(request):
    return {'site': SiteSettings.load()}

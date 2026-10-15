from django.shortcuts import get_object_or_404, render

from apps.base.models import FAQ, Advantage, HeroSlide, Page
from apps.cms.models import Lift, Offer, Post, Review, Room, ServiceCategory, SkiPass, TransferRoute
from apps.cms.utils import slope_conditions, slope_levels, total_slopes_km


def homepage(request):
    return render(request, 'base/home.html', {
        'slides': HeroSlide.objects.filter(is_active=True)[:5],
        'conditions': slope_conditions(),
        'advantages': Advantage.objects.filter(is_active=True),
        'slope_levels': slope_levels(),
        'ski_passes': SkiPass.objects.filter(is_active=True)[:3],
        'rooms': Room.objects.filter(is_active=True)[:3],
        'offers': Offer.objects.current()[:3],
        'service_categories': ServiceCategory.objects.filter(is_active=True)[:4],
        'reviews': Review.objects.filter(is_published=True)[:3],
        'posts': Post.objects.published()[:3],
        'transfer_routes': TransferRoute.objects.filter(is_active=True)[:3],
        'about_page': Page.objects.filter(slug='about', is_published=True).first(),
        'total_km': total_slopes_km(),
        'lifts_count': Lift.objects.filter(is_active=True).count(),
    })


def about(request):
    return render(request, 'base/about.html', {
        'page': Page.objects.filter(slug='about', is_published=True).first(),
        'advantages': Advantage.objects.filter(is_active=True),
        'faqs': FAQ.objects.filter(is_active=True),
        'conditions': slope_conditions(),
        'total_km': total_slopes_km(),
        'lifts_count': Lift.objects.filter(is_active=True).count(),
        'rooms_count': Room.objects.filter(is_active=True).count(),
    })


def page_detail(request, slug):
    page = get_object_or_404(Page, slug=slug, is_published=True)
    return render(request, 'base/page.html', {'page': page})

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.views.generic import DetailView, ListView

from apps.cms.forms import ReviewForm
from apps.cms.models import (
    GalleryImage, Lift, MenuCategory, MenuItem, Offer, Post, Review, Room, Service, ServiceCategory, SkiPass,
    Slope, TransferRoute,
)
from apps.cms.utils import slope_conditions, slope_levels


def slopes(request):
    return render(request, 'cms/slopes.html', {
        'slopes': Slope.objects.filter(is_active=True),
        'lifts': Lift.objects.filter(is_active=True),
        'levels': slope_levels(),
        'conditions': slope_conditions(),
    })


def ski_passes(request):
    return render(request, 'cms/skipass.html', {
        'ski_passes': SkiPass.objects.filter(is_active=True),
    })


class RoomListView(ListView):
    queryset = Room.objects.filter(is_active=True)
    template_name = 'cms/room_list.html'
    context_object_name = 'rooms'


class RoomDetailView(DetailView):
    queryset = Room.objects.filter(is_active=True).prefetch_related('images')
    template_name = 'cms/room_detail.html'
    context_object_name = 'room'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_rooms'] = Room.objects.filter(is_active=True).exclude(pk=self.object.pk)[:3]
        return context


class ServiceCategoryListView(ListView):
    queryset = ServiceCategory.objects.filter(is_active=True)
    template_name = 'cms/service_list.html'
    context_object_name = 'categories'


class ServiceCategoryDetailView(DetailView):
    queryset = ServiceCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('services', queryset=Service.objects.filter(is_active=True)),
    )
    template_name = 'cms/service_category.html'
    context_object_name = 'category'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ServiceCategory.objects.filter(is_active=True)
        return context


def menu(request):
    categories = MenuCategory.objects.filter(is_active=True).prefetch_related(
        Prefetch('items', queryset=MenuItem.objects.filter(is_active=True)),
    )
    return render(request, 'cms/menu.html', {'categories': categories})


def transfer(request):
    return render(request, 'cms/transfer.html', {
        'routes': TransferRoute.objects.filter(is_active=True),
    })


class OfferListView(ListView):
    queryset = Offer.objects.current()
    template_name = 'cms/offer_list.html'
    context_object_name = 'offers'


class OfferDetailView(DetailView):
    queryset = Offer.objects.current()
    template_name = 'cms/offer_detail.html'
    context_object_name = 'offer'


class GalleryView(ListView):
    queryset = GalleryImage.objects.filter(is_active=True)
    template_name = 'cms/gallery.html'
    context_object_name = 'images'


def reviews(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Спасибо за отзыв! Он появится на сайте после проверки.')
            return redirect('cms:reviews')
    else:
        form = ReviewForm()

    page = Paginator(Review.objects.filter(is_published=True), 12).get_page(request.GET.get('page'))
    return render(request, 'cms/reviews.html', {'page_obj': page, 'form': form})


class PostListView(ListView):
    queryset = Post.objects.published()
    template_name = 'cms/post_list.html'
    context_object_name = 'posts'
    paginate_by = 9


class PostDetailView(DetailView):
    queryset = Post.objects.published()
    template_name = 'cms/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['other_posts'] = Post.objects.published().exclude(pk=self.object.pk)[:3]
        return context

from django.urls import path

from apps.cms import views

app_name = 'cms'

urlpatterns = [
    path('slopes/', views.slopes, name='slopes'),
    path('skipass/', views.ski_passes, name='skipass'),
    path('rental/', views.rental, name='rental'),
    path('prices/', views.prices, name='prices'),
    path('rooms/', views.RoomListView.as_view(), name='room_list'),
    path('rooms/<slug:slug>/', views.RoomDetailView.as_view(), name='room_detail'),
    path('services/', views.ServiceCategoryListView.as_view(), name='service_list'),
    path('services/<slug:slug>/', views.ServiceCategoryDetailView.as_view(), name='service_category'),
    path('menu/', views.menu, name='menu'),
    path('transfer/', views.transfer, name='transfer'),
    path('offers/', views.OfferListView.as_view(), name='offer_list'),
    path('offers/<slug:slug>/', views.OfferDetailView.as_view(), name='offer_detail'),
    path('gallery/', views.GalleryView.as_view(), name='gallery'),
    path('reviews/', views.reviews, name='reviews'),
    path('blog/', views.PostListView.as_view(), name='post_list'),
    path('blog/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
]

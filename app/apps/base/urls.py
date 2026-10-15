from django.urls import path

from apps.base import views

app_name = 'base'

urlpatterns = [
    path('', views.homepage, name='home'),
    path('about/', views.about, name='about'),
    path('page/<slug:slug>/', views.page_detail, name='page'),
]

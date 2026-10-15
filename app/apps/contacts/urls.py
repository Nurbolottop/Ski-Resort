from django.urls import path

from apps.contacts import views

app_name = 'contacts'

urlpatterns = [
    path('contacts/', views.contacts, name='contacts'),
    path('booking/', views.booking, name='booking'),
    path('subscribe/', views.subscribe, name='subscribe'),
]

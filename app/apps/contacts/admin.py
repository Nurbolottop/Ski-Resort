from django.contrib import admin

from apps.contacts.models import BookingRequest, ContactMessage, Subscriber


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'check_in', 'check_out', 'adults', 'children', 'room', 'need_transfer', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status', 'need_transfer', 'room')
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'check_in'


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'email', 'is_processed', 'created_at')
    list_editable = ('is_processed',)
    list_filter = ('is_processed',)
    search_fields = ('name', 'phone', 'email', 'message')


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

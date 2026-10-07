from django.contrib import admin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter
from unfold.decorators import action, display

from apps.base.admin_base import BaseAdmin
from apps.contacts.models import BookingRequest, ContactMessage, Subscriber

STATUS_LABELS = {
    BookingRequest.Status.NEW: 'warning',
    BookingRequest.Status.IN_PROGRESS: 'info',
    BookingRequest.Status.CONFIRMED: 'success',
    BookingRequest.Status.CANCELLED: 'danger',
}


@admin.register(BookingRequest)
class BookingRequestAdmin(BaseAdmin):
    list_display = ('guest', 'dates', 'guests', 'room', 'need_transfer', 'status_label', 'created_at')
    list_filter = (('status', ChoicesDropdownFilter), 'need_transfer', ('check_in', RangeDateFilter))
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'check_in'
    actions = ['mark_in_progress', 'mark_confirmed', 'mark_cancelled']
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Гость', {'fields': (('name', 'phone'), 'email')}),
        ('Бронирование', {'fields': (('check_in', 'check_out'), ('adults', 'children'), 'room', 'need_transfer', 'comment')}),
        ('Обработка', {'fields': ('status', ('created_at', 'updated_at'))}),
    )

    @display(description='Гость', header=True)
    def guest(self, obj):
        return [obj.name, obj.phone, ''.join(w[0] for w in obj.name.split()[:2]).upper(), None]

    @display(description='Даты', ordering='check_in')
    def dates(self, obj):
        nights = (obj.check_out - obj.check_in).days
        return f'{obj.check_in:%d.%m} – {obj.check_out:%d.%m.%Y} ({nights} н.)'

    @display(description='Гостей')
    def guests(self, obj):
        return f'{obj.adults} + {obj.children} дет.' if obj.children else obj.adults

    @display(description='Статус', label=STATUS_LABELS, ordering='status')
    def status_label(self, obj):
        return obj.status, obj.get_status_display()

    @action(description='Взять в работу')
    def mark_in_progress(self, request, queryset):
        queryset.update(status=BookingRequest.Status.IN_PROGRESS)

    @action(description='Подтвердить')
    def mark_confirmed(self, request, queryset):
        queryset.update(status=BookingRequest.Status.CONFIRMED)

    @action(description='Отменить')
    def mark_cancelled(self, request, queryset):
        queryset.update(status=BookingRequest.Status.CANCELLED)


@admin.register(ContactMessage)
class ContactMessageAdmin(BaseAdmin):
    list_display = ('author', 'short_message', 'processed_label', 'created_at')
    list_filter = ('is_processed',)
    search_fields = ('name', 'phone', 'email', 'message')
    actions = ['mark_processed']
    readonly_fields = ('created_at',)
    fields = (('name', 'phone', 'email'), 'message', 'is_processed', 'created_at')

    @display(description='Автор', header=True)
    def author(self, obj):
        return [obj.name, obj.phone or obj.email, ''.join(w[0] for w in obj.name.split()[:2]).upper(), None]

    @display(description='Сообщение')
    def short_message(self, obj):
        return obj.message[:90]

    @display(description='Статус', label={'Новое': 'warning', 'Обработано': 'success'})
    def processed_label(self, obj):
        return 'Обработано' if obj.is_processed else 'Новое'

    @action(description='Отметить обработанными')
    def mark_processed(self, request, queryset):
        queryset.update(is_processed=True)


@admin.register(Subscriber)
class SubscriberAdmin(BaseAdmin):
    list_display = ('email', 'created_at')
    search_fields = ('email',)

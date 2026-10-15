"""Дашборд, бейджи и метка окружения для админки Unfold."""
from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from apps.base.models import SiteSettings
from apps.cms.models import Review
from apps.cms.utils import slope_conditions
from apps.contacts.models import BookingRequest, ContactMessage, Subscriber


def _count_or_none(count):
    return str(count) if count else None


def badge_new_bookings(request):
    return _count_or_none(BookingRequest.objects.filter(status=BookingRequest.Status.NEW).count())


def badge_new_messages(request):
    return _count_or_none(ContactMessage.objects.filter(is_processed=False).count())


def badge_pending_reviews(request):
    return _count_or_none(Review.objects.filter(is_published=False).count())


def environment_callback(request):
    site = SiteSettings.load()
    if not site.is_season_open:
        return ['Межсезонье', 'warning']
    if site.is_open_today:
        return ['Сегодня работаем', 'success']
    return [f'Работаем {site.open_days_label}', 'info']


def dashboard_callback(request, context):
    site = SiteSettings.load()
    today = timezone.localdate()
    week_ago = timezone.now() - timedelta(days=7)

    bookings = BookingRequest.objects.select_related('room')
    upcoming = bookings.filter(check_in__gte=today).exclude(status=BookingRequest.Status.CANCELLED)

    context.update({
        'site': site,
        'conditions': slope_conditions(),
        'kpi': [
            {
                'title': 'Новые заявки',
                'value': bookings.filter(status=BookingRequest.Status.NEW).count(),
                'note': f'+{bookings.filter(created_at__gte=week_ago).count()} за 7 дней',
                'icon': 'event_available',
                'url': reverse('admin:contacts_bookingrequest_changelist') + '?status__exact=new',
            },
            {
                'title': 'Предстоящие заезды',
                'value': upcoming.count(),
                'note': 'без отменённых',
                'icon': 'luggage',
                'url': reverse('admin:contacts_bookingrequest_changelist'),
            },
            {
                'title': 'Сообщения',
                'value': ContactMessage.objects.filter(is_processed=False).count(),
                'note': 'не обработаны',
                'icon': 'mail',
                'url': reverse('admin:contacts_contactmessage_changelist') + '?is_processed__exact=0',
            },
            {
                'title': 'Отзывы на модерации',
                'value': Review.objects.filter(is_published=False).count(),
                'note': f'подписчиков: {Subscriber.objects.count()}',
                'icon': 'reviews',
                'url': reverse('admin:cms_review_changelist') + '?is_published__exact=0',
            },
        ],
        'latest_bookings': bookings[:8],
        'booking_statuses': dict(BookingRequest.Status.choices),
    })
    return context

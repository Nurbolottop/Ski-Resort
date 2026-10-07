"""Настройки админки (django-unfold)."""
from django.conf import settings
from django.templatetags.static import static
from django.urls import reverse_lazy


def _item(title, icon, url_name, badge=None):
    item = {'title': title, 'icon': icon, 'link': reverse_lazy(url_name)}
    if badge:
        item['badge'] = badge
    return item


UNFOLD = {
    'SITE_TITLE': 'Тоо-Ашуу',
    'SITE_HEADER': 'Тоо-Ашуу',
    'SITE_SUBHEADER': 'Управление сайтом',
    'SITE_URL': '/',
    'SITE_SYMBOL': 'landscape',
    'SITE_FAVICONS': [
        {'rel': 'icon', 'sizes': 'any', 'type': 'image/svg+xml', 'href': lambda request: static('img/favicon.svg')},
    ],
    'SHOW_HISTORY': True,
    'SHOW_VIEW_ON_SITE': True,
    'SHOW_BACK_BUTTON': True,
    'ENVIRONMENT': 'apps.base.admin_dashboard.environment_callback',
    'DASHBOARD_CALLBACK': 'apps.base.admin_dashboard.dashboard_callback',
    'STYLES': [lambda request: f"{static('css/admin-dashboard.css')}?v={settings.ASSET_VERSION}"],
    'LOGIN': {
        'image': lambda request: static('img/admin-login.svg'),
    },
    'COLORS': {
        # Фирменный синий «Тоо-Ашуу» (#1f46a0) — основной цвет админки
        'primary': {
            '50': 'oklch(97% .014 254.604)',
            '100': 'oklch(93.2% .032 255.585)',
            '200': 'oklch(88.2% .059 254.128)',
            '300': 'oklch(80.9% .105 251.813)',
            '400': 'oklch(70.7% .165 254.624)',
            '500': 'oklch(62.3% .214 259.815)',
            '600': 'oklch(48% .19 263)',
            '700': 'oklch(42.4% .17 265)',
            '800': 'oklch(37.9% .146 265.522)',
            '900': 'oklch(32% .12 266)',
            '950': 'oklch(28.2% .091 267.935)',
        },
    },
    'SIDEBAR': {
        'show_search': True,
        'show_all_applications': True,
        'navigation': [
            {
                'title': 'Главное',
                'items': [
                    _item('Дашборд', 'space_dashboard', 'admin:index'),
                    _item('Настройки сайта', 'tune', 'admin:base_sitesettings_changelist'),
                ],
            },
            {
                'title': 'Заявки',
                'separator': True,
                'items': [
                    _item('Бронирования', 'event_available', 'admin:contacts_bookingrequest_changelist',
                          'apps.base.admin_dashboard.badge_new_bookings'),
                    _item('Сообщения', 'mail', 'admin:contacts_contactmessage_changelist',
                          'apps.base.admin_dashboard.badge_new_messages'),
                    _item('Подписчики', 'alternate_email', 'admin:contacts_subscriber_changelist'),
                ],
            },
            {
                'title': 'Склон',
                'separator': True,
                'items': [
                    _item('Трассы', 'downhill_skiing', 'admin:cms_slope_changelist'),
                    _item('Подъёмники', 'airline_seat_recline_normal', 'admin:cms_lift_changelist'),
                    _item('Ски-пассы', 'confirmation_number', 'admin:cms_skipass_changelist'),
                    _item('Прокат', 'snowboarding', 'admin:cms_rentalitem_changelist'),
                ],
            },
            {
                'title': 'Отдых',
                'separator': True,
                'items': [
                    _item('Номера и жильё', 'bed', 'admin:cms_room_changelist'),
                    _item('Услуги', 'room_service', 'admin:cms_servicecategory_changelist'),
                    _item('Меню', 'restaurant_menu', 'admin:cms_menucategory_changelist'),
                    _item('Трансфер', 'airport_shuttle', 'admin:cms_transferroute_changelist'),
                ],
            },
            {
                'title': 'Контент',
                'separator': True,
                'items': [
                    _item('Слайды главной', 'view_carousel', 'admin:base_heroslide_changelist'),
                    _item('Преимущества', 'verified', 'admin:base_advantage_changelist'),
                    _item('Акции', 'sell', 'admin:cms_offer_changelist'),
                    _item('Галерея', 'photo_library', 'admin:cms_galleryimage_changelist'),
                    _item('Альбомы', 'collections', 'admin:cms_galleryalbum_changelist'),
                    _item('Отзывы', 'reviews', 'admin:cms_review_changelist',
                          'apps.base.admin_dashboard.badge_pending_reviews'),
                    _item('Блог', 'article', 'admin:cms_post_changelist'),
                    _item('Вопросы и ответы', 'help', 'admin:base_faq_changelist'),
                    _item('Страницы', 'description', 'admin:base_page_changelist'),
                ],
            },
            {
                'title': 'Доступ',
                'separator': True,
                'items': [
                    _item('Пользователи', 'person', 'admin:auth_user_changelist'),
                    _item('Группы', 'group', 'admin:auth_group_changelist'),
                ],
            },
        ],
    },
}

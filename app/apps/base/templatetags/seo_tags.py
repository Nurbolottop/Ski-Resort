"""Schema.org (JSON-LD): данные о базе для поисковиков и ИИ-ассистентов. Всё берётся из БД."""
import json
import re

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from apps.base.models import FAQ, SiteSettings
from apps.base.seo import STATIC_PAGES
from apps.cms.models import MenuCategory, RentalItem, Room, SkiPass, TransferRoute

register = template.Library()

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
ALT_NAMES = ['Baytur', 'Байтур', 'Тоо-Ашуу', 'Too-Ashuu', 'Горнолыжная база Тоо-Ашуу', 'Baytur Ski']
# Страница-деталь → её раздел (для хлебных крошек)
PARENTS = {
    'cms:room_detail': 'cms:room_list',
    'cms:service_category': 'cms:service_list',
    'cms:offer_detail': 'cms:offer_list',
    'cms:post_detail': 'cms:post_list',
}


def _script(data):
    raw = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    return mark_safe(f'<script type="application/ld+json">{raw}</script>')


def _text(html):
    return re.sub(r'\s+', ' ', strip_tags(html or '')).strip()


def _abs(request, url):
    return request.build_absolute_uri(url)


def _resort_id(request):
    return _abs(request, '/') + '#resort'


def _offer(name, price, unit='', description=''):
    data = {'@type': 'Offer', 'name': name, 'price': price, 'priceCurrency': 'KGS'}
    if unit:
        data['priceSpecification'] = {'@type': 'UnitPriceSpecification', 'price': price,
                                      'priceCurrency': 'KGS', 'unitText': unit}
    if description:
        data['description'] = description
    return data


def resort_description(site):
    parts = [f'{site.name} — горнолыжная база на перевале Тоо-Ашуу в Кыргызстане']
    if site.altitude_top:
        parts.append(f'на высоте до {site.altitude_top} м')
    if site.distance_km:
        parts.append(f'в {site.distance_km} км от Бишкека по трассе Бишкек — Ош')
    return (', '.join(parts) + '. Горнолыжные трассы и подъёмник, ски-пассы, прокат лыж и сноубордов, '
            'проживание в коттеджах, кафе и трансфер из Бишкека.')


def _resort(request, site):
    base = _abs(request, '/')
    data = {
        '@type': 'SkiResort',
        '@id': _resort_id(request),
        'name': site.full_name or site.name,
        'alternateName': [n for n in ALT_NAMES if n != (site.full_name or site.name)],
        'description': resort_description(site),
        'url': base,
        'image': [_abs(request, static(f'img/photos/{p}.jpg')) for p in ('panorama', 'slopes', 'chalet', 'lift')],
        'address': {
            '@type': 'PostalAddress',
            'streetAddress': site.address or 'Перевал Тоо-Ашуу, трасса Бишкек — Ош',
            'addressLocality': 'Перевал Тоо-Ашуу',
            'addressRegion': 'Чуйская область',
            'addressCountry': 'KG',
        },
        'containedInPlace': {'@type': 'Place', 'name': 'Перевал Тоо-Ашуу, Киргизский хребет'},
        'currenciesAccepted': 'KGS',
        'publicAccess': True,
        'isAccessibleForFree': False,
    }
    if site.logo:
        data['logo'] = _abs(request, site.logo.url)
    if site.phone:
        data['telephone'] = site.phone
    if site.email:
        data['email'] = site.email
    contacts = [('администратор базы', site.phone), ('администратор базы', site.phone_2),
                ('бронирование (WhatsApp)', site.whatsapp), ('трансфер', site.transfer_phone)]
    data['contactPoint'] = [{'@type': 'ContactPoint', 'contactType': t, 'telephone': p,
                             'availableLanguage': ['ru', 'ky']} for t, p in contacts if p]
    if site.latitude and site.longitude:
        lat, lng = float(site.latitude), float(site.longitude)
        data['geo'] = {'@type': 'GeoCoordinates', 'latitude': lat, 'longitude': lng}
        data['hasMap'] = f'https://www.google.com/maps?q={lat},{lng}'
    if site.altitude_top:
        data['geo'] = {**data.get('geo', {'@type': 'GeoCoordinates'}), 'elevation': site.altitude_top}
    prices = list(SkiPass.objects.filter(is_active=True).values_list('price', flat=True))
    if prices:
        data['priceRange'] = f'{min(prices)}–{max(prices)} сом'
    times = re.findall(r'(\d{1,2})[:.](\d{2})', site.lift_hours or '')
    if len(times) >= 2 and site.open_days:
        (h1, m1), (h2, m2) = times[:2]
        data['openingHoursSpecification'] = [{
            '@type': 'OpeningHoursSpecification',
            'dayOfWeek': [DAYS[d] for d in site.open_days if d < 7],
            'opens': f'{int(h1):02d}:{m1}', 'closes': f'{int(h2):02d}:{m2}',
        }]
    amenities = ['Горнолыжные трассы', 'Подъёмник']
    if RentalItem.objects.filter(is_active=True).exists():
        amenities.append('Прокат лыж и сноубордов')
    if Room.objects.filter(is_active=True).exists():
        amenities.append('Проживание в коттеджах')
    if MenuCategory.objects.filter(is_active=True).exists():
        amenities.append('Кафе')
    if TransferRoute.objects.filter(is_active=True).exists():
        amenities.append('Трансфер из Бишкека')
    data['amenityFeature'] = [{'@type': 'LocationFeatureSpecification', 'name': a, 'value': True}
                              for a in amenities]
    data['sameAs'] = [u for u in (site.instagram, site.telegram, site.facebook) if u]
    return data


def _breadcrumbs(request, title):
    match = request.resolver_match
    if not match or match.view_name == 'base:home':
        return None
    names = dict(STATIC_PAGES)
    crumbs = [('Главная', reverse('base:home'))]
    parent = PARENTS.get(match.view_name)
    if parent:
        crumbs.append((names[parent], reverse(parent)))
    crumbs.append((names.get(match.view_name) or title, request.path))
    return {'@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': i, 'name': n, 'item': _abs(request, u)}
        for i, (n, u) in enumerate(crumbs, 1)]}


@register.simple_tag(takes_context=True)
def jsonld_site(context, title=''):
    """На каждой странице: база (SkiResort), сайт и хлебные крошки."""
    request = context['request']
    site = context.get('site') or SiteSettings.load()
    graph = [_resort(request, site), {
        '@type': 'WebSite', '@id': _abs(request, '/') + '#website', 'url': _abs(request, '/'),
        'name': site.full_name or site.name, 'alternateName': ALT_NAMES, 'inLanguage': 'ru',
        'publisher': {'@id': _resort_id(request)},
    }]
    crumbs = _breadcrumbs(request, title)
    if crumbs:
        graph.append(crumbs)
    return _script({'@context': 'https://schema.org', '@graph': graph})


def _catalog(request, name, offers):
    return {'@type': 'OfferCatalog', 'name': name, 'provider': {'@id': _resort_id(request)},
            'itemListElement': offers}


def _skipass_catalog(request):
    return _catalog(request, 'Ски-пассы', [
        _offer(p.name, p.price, p.price_unit, p.note)
        for p in SkiPass.objects.filter(is_active=True)])


def _rental_catalog(request):
    offers = []
    for item in RentalItem.objects.filter(is_active=True):
        name = f'Прокат: {item.name} ({item.get_category_display().lower()})'
        if item.price_day:
            offers.append(_offer(name, item.price_day, 'день', item.description))
        elif item.price_hour:
            offers.append(_offer(name, item.price_hour, 'час', item.description))
    return _catalog(request, 'Прокат снаряжения', offers)


def _room(request, room, full=False):
    data = {
        '@type': ['HotelRoom', 'Product'],
        'name': room.name,
        'url': _abs(request, room.get_absolute_url()),
        'description': _text(room.short_description) or room.name,
        'occupancy': {'@type': 'QuantitativeValue', 'maxValue': room.max_guests},
        'containedInPlace': {'@id': _resort_id(request)},
        'offers': _offer(room.name, room.price_from, room.price_unit or 'ночь'),
    }
    if room.cover:
        data['image'] = _abs(request, room.cover.url)
    if full:
        if room.area:
            data['floorSize'] = {'@type': 'QuantitativeValue', 'value': room.area, 'unitCode': 'MTK'}
        if room.beds:
            data['bed'] = room.beds
        amenities = [a.strip() for a in (room.amenities or '').splitlines() if a.strip()]
        if amenities:
            data['amenityFeature'] = [{'@type': 'LocationFeatureSpecification', 'name': a, 'value': True}
                                      for a in amenities]
    return data


def _rooms_list(request):
    return {'@type': 'ItemList', 'name': 'Проживание на базе',
            'itemListElement': [{'@type': 'ListItem', 'position': i, 'item': _room(request, r)}
                                for i, r in enumerate(Room.objects.filter(is_active=True), 1)]}


@register.simple_tag(takes_context=True)
def jsonld(context, kind, obj=None):
    """Данные конкретной страницы: цены, номера, меню, FAQ, статьи."""
    request = context['request']
    if kind == 'faq':
        faqs = FAQ.objects.filter(is_active=True)
        if not faqs:
            return ''
        data = {'@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': f.question,
             'acceptedAnswer': {'@type': 'Answer', 'text': _text(f.answer)}} for f in faqs]}
    elif kind == 'skipass':
        data = _skipass_catalog(request)
    elif kind == 'rental':
        data = _rental_catalog(request)
    elif kind == 'rooms':
        data = _rooms_list(request)
    elif kind == 'room':
        data = _room(request, obj, full=True)
    elif kind == 'prices':
        data = {'@graph': [_skipass_catalog(request), _rental_catalog(request), _rooms_list(request)]}
    elif kind == 'menu':
        data = {'@type': 'Menu', 'name': 'Меню кафе', 'inLanguage': 'ru',
                'hasMenuSection': [{
                    '@type': 'MenuSection', 'name': c.name,
                    'hasMenuItem': [{'@type': 'MenuItem', 'name': i.name,
                                     **({'description': i.description} if i.description else {}),
                                     'offers': {'@type': 'Offer', 'price': i.price, 'priceCurrency': 'KGS'}}
                                    for i in c.items.filter(is_active=True)]}
                    for c in MenuCategory.objects.filter(is_active=True)]}
    elif kind == 'transfer':
        data = {'@graph': [{
            '@type': 'Service', 'serviceType': 'Трансфер', 'name': r.name,
            'provider': {'@id': _resort_id(request)}, 'areaServed': 'Бишкек',
            'description': ' · '.join(v for v in (r.departure_point, r.schedule, r.duration, _text(r.description)) if v),
            **({'offers': _offer(r.name, r.price, r.price_unit)} if r.price else {}),
        } for r in TransferRoute.objects.filter(is_active=True)]}
    elif kind == 'post':
        site = context.get('site') or SiteSettings.load()
        data = {'@type': 'BlogPosting', 'headline': obj.title,
                'description': _text(obj.seo_description or obj.excerpt)[:300],
                'datePublished': obj.published_at.isoformat(), 'dateModified': obj.updated_at.isoformat(),
                'mainEntityOfPage': _abs(request, obj.get_absolute_url()), 'inLanguage': 'ru',
                'author': {'@type': 'Organization', 'name': site.full_name or site.name, 'url': _abs(request, '/')},
                'publisher': {'@id': _resort_id(request)}}
        if obj.cover:
            data['image'] = _abs(request, obj.cover.url)
    elif kind == 'offer':
        data = {'@type': 'Offer', 'name': obj.title, 'url': _abs(request, obj.get_absolute_url()),
                'description': _text(obj.seo_description or obj.short_description),
                'offeredBy': {'@id': _resort_id(request)}}
        if obj.valid_from:
            data['validFrom'] = obj.valid_from.isoformat()
        if obj.valid_to:
            data['validThrough'] = obj.valid_to.isoformat()
    else:
        return ''
    return _script({'@context': 'https://schema.org', **data})

"""robots.txt, sitemap.xml и llms.txt — для поисковиков и ИИ-агентов."""
import os
import re
from datetime import datetime
from datetime import timezone as dt_timezone
from xml.sax.saxutils import escape

from django.db.models import Max
from django.http import HttpResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_page

from apps.base.models import FAQ, HeroSlide, Page, SiteSettings
from apps.base.templatetags.site_tags import PHOTO_ALTS
from apps.cms.models import (GalleryImage, Lift, MenuCategory, MenuItem, Offer, Post, RentalItem, Room, Service,
                             ServiceCategory, SkiPass, Slope, TransferRoute)

# Служебные страницы: не индексируются и не попадают в sitemap
NOINDEX_PAGES = {'privacy', 'offer', 'photo-credits'}

# (имя URL, название, шаблон, фото в шапке, приоритет)
SECTIONS = [
    ('base:home', 'Главная', 'base/home.html', 'panorama', '1.0'),
    ('base:about', 'О базе', 'base/about.html', 'about', '0.8'),
    ('cms:slopes', 'Трассы и подъёмники', 'cms/slopes.html', 'slopes', '0.9'),
    ('cms:skipass', 'Ски-пассы', 'cms/skipass.html', 'skipass', '0.9'),
    ('cms:prices', 'Цены', 'cms/prices.html', 'prices', '0.9'),
    ('cms:rental', 'Прокат снаряжения', 'cms/rental.html', 'rental', '0.8'),
    ('cms:room_list', 'Проживание', 'cms/room_list.html', 'rooms', '0.9'),
    ('cms:service_list', 'Услуги', 'cms/service_list.html', 'services', '0.7'),
    ('cms:menu', 'Меню кафе', 'cms/menu.html', 'menu', '0.6'),
    ('cms:transfer', 'Трансфер', 'cms/transfer.html', 'transfer', '0.8'),
    ('cms:offer_list', 'Акции', 'cms/offer_list.html', 'offers', '0.6'),
    ('cms:gallery', 'Галерея', 'cms/gallery.html', 'gallery', '0.6'),
    ('cms:reviews', 'Отзывы', 'cms/reviews.html', 'reviews', '0.6'),
    ('cms:post_list', 'Новости', 'cms/post_list.html', 'news', '0.6'),
    ('contacts:contacts', 'Контакты', 'contacts/contacts.html', 'contacts', '0.8'),
    ('contacts:booking', 'Бронирование', 'contacts/booking.html', 'chalet', '0.7'),
]
STATIC_PAGES = [(name, title) for name, title, *_ in SECTIONS]

# Ключ IndexNow: файл /<ключ>.txt подтверждает, что сайт наш
INDEXNOW_KEY = '57dd948e21d0a599b52306b8aa3c4f15'


def indexnow_key(request):
    return HttpResponse(INDEXNOW_KEY, content_type='text/plain; charset=utf-8')


def _template_date(name):
    """Дата последнего изменения шаблона — для lastmod страниц без своей даты в БД."""
    try:
        path = get_template(name).origin.name
        return datetime.fromtimestamp(os.path.getmtime(path), tz=dt_timezone.utc)
    except (TemplateDoesNotExist, OSError):
        return None


def _latest(*dates):
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def _dynamic_pages():
    """(url, название, дата изменения) всех опубликованных объектов."""
    room_date = _template_date('cms/room_detail.html')
    service_date = _template_date('cms/service_category.html')
    items = []
    for obj in Room.objects.filter(is_active=True):
        items.append((obj.get_absolute_url(), obj.name, room_date))
    for obj in ServiceCategory.objects.filter(is_active=True):
        items.append((obj.get_absolute_url(), obj.name, service_date))
    for obj in Offer.objects.current():
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    for obj in Post.objects.published():
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    for obj in Page.objects.filter(is_published=True).exclude(slug='about').exclude(slug__in=NOINDEX_PAGES):
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    return items


def _photo(request, name):
    return request.build_absolute_uri(static(f'img/photos/{name}.jpg')), PHOTO_ALTS.get(name, '')


def _media(request, image):
    return request.build_absolute_uri(image.url)


def _page_images(request, name, photo):
    """Картинки страницы для sitemap: (url, подпись)."""
    images = []
    if name == 'base:home':
        images += [(_media(request, s.image), s.image_alt or s.text or s.title)
                   for s in HeroSlide.objects.filter(is_active=True) if s.image]
    elif name == 'cms:gallery':
        images += [(_media(request, i.image), i.caption or f'{i.album.title if i.album else "Горнолыжная база"} — Тоо-Ашуу')
                   for i in GalleryImage.objects.filter(is_active=True).select_related('album')[:100] if i.image]
    elif name == 'cms:room_list':
        images += [(_media(request, r.cover), r.name) for r in Room.objects.filter(is_active=True) if r.cover]
    elif name == 'cms:slopes':
        images.append(_photo(request, 'lift'))
    images.append(_photo(request, photo))
    return images


def _image_xml(images):
    return ''.join(f'<image:image><image:loc>{escape(u)}</image:loc>'
                   f'<image:title>{escape(t)}</image:title></image:image>' for u, t in images)


# Поисковые и ИИ-боты: явно разрешаем читать сайт, чтобы ассистенты знали о базе
BOTS = [
    'Googlebot', 'Google-Extended', 'Yandex', 'Bingbot', 'Applebot-Extended',
    'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'PerplexityBot', 'Perplexity-User',
    'DuckAssistBot', 'meta-externalagent',
]
DISALLOW = ['/admin/', '/subscribe/']
CLEAN_PARAM = 'Clean-param: utm_source&utm_medium&utm_campaign&utm_content&utm_term&fbclid&gclid&yclid /'


def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse('sitemap'))
    lines = []
    for bot in ['*'] + BOTS:
        lines += [f'User-agent: {bot}', 'Allow: /'] + [f'Disallow: {d}' for d in DISALLOW]
        if bot in ('*', 'Yandex'):
            lines.append(CLEAN_PARAM)
        lines.append('')
    lines += [f'Sitemap: {sitemap}', '']
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


@cache_page(60 * 60)
def sitemap_xml(request):
    base = request.build_absolute_uri('/')[:-1]
    site_date = SiteSettings.load().conditions_updated_at
    post_date = Post.objects.published().aggregate(d=Max('updated_at'))['d']
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
           'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    for name, _, template, photo, priority in SECTIONS:
        updated = _latest(_template_date(template), site_date if name in ('base:home', 'contacts:contacts') else None,
                          post_date if name in ('base:home', 'cms:post_list') else None)
        out.append(f'  <url><loc>{base}{reverse(name)}</loc><lastmod>{updated:%Y-%m-%d}</lastmod>'
                   f'<priority>{priority}</priority>{_image_xml(_page_images(request, name, photo))}</url>')
    for url, title, updated in _dynamic_pages():
        images = []
        if url.startswith('/rooms/'):
            room = Room.objects.filter(slug=url.strip('/').split('/')[-1]).first()
            if room:
                if room.cover:
                    images.append((_media(request, room.cover), room.name))
                images += [(_media(request, i.image), f'{room.name} — фото {n}')
                           for n, i in enumerate(room.images.all(), 1) if i.image]
                if not images:
                    images.append(_photo(request, 'chalet'))
        updated = updated or _template_date('base.html')
        out.append(f'  <url><loc>{base}{url}</loc><lastmod>{updated:%Y-%m-%d}</lastmod>'
                   f'<priority>0.7</priority>{_image_xml(images)}</url>')
    out.append('</urlset>')
    return HttpResponse('\n'.join(out), content_type='application/xml; charset=utf-8')


def _plain(html):
    html = re.sub(r'</(p|li|h[1-6])>|<br\s*/?>', ' ', html or '')
    return re.sub(r'\s+', ' ', strip_tags(html)).strip()


def _som(value, unit=''):
    text = f'{value:,}'.replace(',', ' ') + ' сом'
    return f'{text} / {unit}' if unit else text


@cache_page(60 * 15)
def llms_txt(request):
    """Справка о базе для ИИ-ассистентов."""
    from apps.base.templatetags.seo_tags import ALT_NAMES, resort_description

    site = SiteSettings.load()
    base = request.build_absolute_uri('/')[:-1]
    name = site.full_name or site.name
    out = [f'# {name} (Тоо-Ашуу)', '', f'> {resort_description(site)}', '',
           'Другие названия: ' + ', '.join(ALT_NAMES) + '.', '',
           f'Официальный сайт: {base}/', '']

    facts = [f'Расположение: {site.address or "перевал Тоо-Ашуу, трасса Бишкек — Ош"}, Чуйская область, Кыргызстан']
    if site.latitude and site.longitude:
        facts.append(f'Координаты: {site.latitude}, {site.longitude}')
    if site.altitude_top:
        facts.append(f'Высота: до {site.altitude_top} м над уровнем моря')
    if site.distance_km:
        facts.append(f'Расстояние от Бишкека: {site.distance_km} км, около 2,5 часов на машине')
    if site.open_days:
        hours = f', {site.lift_hours}' if site.lift_hours else ''
        facts.append(f'Подъёмники работают: {site.open_days_label}{hours}')
    if site.season:
        facts.append(f'Сезон: {site.season}')
    facts.append('Сезон сейчас: ' + ('открыт' if site.is_season_open else 'закрыт (межсезонье)'))
    if site.snow_depth is not None:
        facts.append(f'Высота снега: {site.snow_depth} см' + (f' ({site.snow_note})' if site.snow_note else ''))
    out += ['## Коротко о базе', ''] + [f'- {f}' for f in facts] + ['']

    contacts = [(t, v) for t, v in (
        ('Администратор', site.phone), ('Администратор (WhatsApp)', site.phone_2),
        ('Бронирование (WhatsApp)', site.whatsapp), ('E-mail', site.email),
        ('Instagram', site.instagram), ('Telegram', site.telegram)) if v]
    if site.transfer_phone:
        contacts.append(('Трансфер', f'{site.transfer_phone}' + (f' ({site.transfer_contact})' if site.transfer_contact else '')))
    out += ['## Контакты', ''] + [f'- {t}: {v}' for t, v in contacts]
    out += [f'- Онлайн-заявка на бронирование: {base}{reverse("contacts:booking")}', '']

    slopes = Slope.objects.filter(is_active=True)
    if slopes:
        out += ['## Трассы', '']
        for s in slopes:
            info = [s.get_level_display().lower() + ' трасса']
            if s.length_m:
                info.append(f'длина {s.length_m} м')
            if s.vertical_drop_m:
                info.append(f'перепад {s.vertical_drop_m} м')
            if s.steepness:
                info.append(f'уклон до {s.steepness}°')
            out.append(f'- {s.name}: ' + ', '.join(info))
        out.append('')
    lifts = Lift.objects.filter(is_active=True)
    if lifts:
        out += ['## Подъёмники', '']
        for l in lifts:
            info = [l.get_lift_type_display().lower()]
            if l.length_m:
                info.append(f'длина {l.length_m} м')
            if l.ride_minutes:
                info.append(f'подъём {l.ride_minutes} мин')
            if l.hours:
                info.append(f'работает {l.hours}')
            out.append(f'- {l.name}: ' + ', '.join(info))
        out.append('')

    passes = SkiPass.objects.filter(is_active=True)
    if passes:
        out += ['## Ски-пассы (цены в кыргызских сомах)', '']
        out += [f'- {p.name}: {_som(p.price, p.price_unit)}' + (f' — {p.note}' if p.note else '') for p in passes]
        out += [f'- Подробнее: {base}{reverse("cms:skipass")}', '']

    rental = RentalItem.objects.filter(is_active=True)
    if rental:
        out += ['## Прокат снаряжения', '']
        for r in rental:
            prices = [_som(r.price_day, 'день') if r.price_day else '', _som(r.price_hour, 'час') if r.price_hour else '']
            line = f'- {r.name} ({r.get_category_display().lower()})'
            if any(prices):
                line += ': ' + ', '.join(p for p in prices if p)
            out.append(line + (f'. {r.description}' if r.description else ''))
        out += [f'- Подробнее: {base}{reverse("cms:rental")}', '']

    rooms = Room.objects.filter(is_active=True)
    if rooms:
        out += ['## Проживание', '']
        for r in rooms:
            line = f'- [{r.name}]({base}{r.get_absolute_url()}): до {r.max_guests} гостей, от {_som(r.price_from, r.price_unit)}'
            out.append(line + (f'. {_plain(r.short_description)}' if r.short_description else ''))
        out.append('')

    routes = TransferRoute.objects.filter(is_active=True)
    out += ['## Как добраться', '']
    if site.directions:
        out += [_plain(site.directions), '']
    for r in routes:
        info = [v for v in (r.departure_point, r.schedule, r.duration) if v]
        info.append(_som(r.price, r.price_unit) if r.price else 'цена по запросу')
        out.append(f'- {r.name}: ' + ', '.join(info) + (f'. {_plain(r.description)}' if r.description else ''))
    out += [f'- Подробнее: {base}{reverse("cms:transfer")}', '']

    services = Service.objects.filter(is_active=True, category__is_active=True)
    if services:
        out += ['## Услуги', '']
        out += [f'- {s.name}' + (f': {s.price}' if s.price else '') + (f'. {_plain(s.description)}' if s.description else '')
                for s in services]
        out.append('')

    cats = MenuCategory.objects.filter(is_active=True)
    if cats:
        out += ['## Кафе', '', 'Разделы меню: ' + ', '.join(c.name for c in cats) + '.']
        hits = MenuItem.objects.filter(is_active=True, is_hit=True)[:10]
        if hits:
            out.append('Хиты: ' + ', '.join(f'{i.name} — {_som(i.price)}' for i in hits) + '.')
        out += [f'Полное меню с ценами: {base}{reverse("cms:menu")}', '']

    faqs = FAQ.objects.filter(is_active=True)
    if faqs:
        out += ['## Частые вопросы', '']
        for f in faqs:
            out += [f'### {f.question}', '', _plain(f.answer), '']

    out += ['## Разделы сайта', '']
    out += [f'- [{title}]({base}{reverse(n)})' for n, title in STATIC_PAGES]
    dynamic = _dynamic_pages()
    if dynamic:
        out += ['', '## Страницы', '']
        out += [f'- [{title}]({base}{url})' for url, title, _ in dynamic]
    out.append('')
    return HttpResponse('\n'.join(out), content_type='text/plain; charset=utf-8')

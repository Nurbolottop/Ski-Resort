"""robots.txt, sitemap.xml и llms.txt — для поисковиков и ИИ-агентов."""
import re

from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_page

from apps.base.models import FAQ, Page, SiteSettings
from apps.cms.models import (Lift, MenuCategory, MenuItem, Offer, Post, RentalItem, Room, Service,
                             ServiceCategory, SkiPass, Slope, TransferRoute)

STATIC_PAGES = [
    ('base:home', 'Главная'),
    ('base:about', 'О базе'),
    ('cms:slopes', 'Трассы и подъёмники'),
    ('cms:skipass', 'Ски-пассы'),
    ('cms:prices', 'Цены'),
    ('cms:rental', 'Прокат снаряжения'),
    ('cms:room_list', 'Проживание'),
    ('cms:service_list', 'Услуги'),
    ('cms:menu', 'Меню кафе'),
    ('cms:transfer', 'Трансфер'),
    ('cms:offer_list', 'Акции'),
    ('cms:gallery', 'Галерея'),
    ('cms:reviews', 'Отзывы'),
    ('cms:post_list', 'Новости'),
    ('contacts:contacts', 'Контакты'),
    ('contacts:booking', 'Бронирование'),
]


def _dynamic_pages():
    """(url, название, дата изменения) всех опубликованных объектов."""
    items = []
    for obj in Room.objects.filter(is_active=True):
        items.append((obj.get_absolute_url(), obj.name, None))
    for obj in ServiceCategory.objects.filter(is_active=True):
        items.append((obj.get_absolute_url(), obj.name, None))
    for obj in Offer.objects.current():
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    for obj in Post.objects.published():
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    for obj in Page.objects.filter(is_published=True).exclude(slug='about'):
        items.append((obj.get_absolute_url(), obj.title, obj.updated_at))
    return items


# ИИ-ассистенты и поисковые боты, которым явно разрешено читать сайт
AI_BOTS = [
    'GPTBot', 'OAI-SearchBot', 'ChatGPT-User', 'ClaudeBot', 'Claude-SearchBot', 'Claude-User',
    'PerplexityBot', 'Perplexity-User', 'Google-Extended', 'Applebot-Extended', 'YandexAdditional',
    'Bingbot', 'DuckAssistBot', 'meta-externalagent',
]


def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse('sitemap'))
    lines = []
    for bot in ['*'] + AI_BOTS:
        lines += [f'User-agent: {bot}', 'Allow: /', 'Disallow: /admin/', 'Disallow: /subscribe/', '']
    lines += [
        'Clean-param: utm_source&utm_medium&utm_campaign&utm_content&utm_term&fbclid&gclid&yclid',
        '',
        f'Sitemap: {sitemap}',
        '',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


@cache_page(60 * 60)
def sitemap_xml(request):
    base = request.build_absolute_uri('/')[:-1]
    urls = [(reverse(name), None) for name, _ in STATIC_PAGES]
    urls += [(url, updated) for url, _, updated in _dynamic_pages()]
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, updated in urls:
        lastmod = f'<lastmod>{updated:%Y-%m-%d}</lastmod>' if updated else ''
        out.append(f'  <url><loc>{base}{url}</loc>{lastmod}</url>')
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

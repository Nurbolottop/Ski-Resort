"""robots.txt, sitemap.xml и llms.txt — для поисковиков и ИИ-агентов."""
from django.http import HttpResponse
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_page

from apps.base.models import Page, SiteSettings
from apps.cms.models import Offer, Post, Room, ServiceCategory

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


def robots_txt(request):
    sitemap = request.build_absolute_uri(reverse('sitemap'))
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /subscribe/',
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


@cache_page(60 * 60)
def llms_txt(request):
    site = SiteSettings.load()
    base = request.build_absolute_uri('/')[:-1]
    name = site.full_name or site.name
    out = [f'# {name}', '']
    if site.tagline:
        out += [f'> {strip_tags(site.tagline)}', '']
    contacts = [v for v in (getattr(site, 'phone', ''), getattr(site, 'address', ''),
                            getattr(site, 'instagram', '')) if v]
    if contacts:
        out += ['Контакты: ' + ' · '.join(contacts), '']
    out += ['## Разделы', '']
    out += [f'- [{title}]({base}{reverse(n)})' for n, title in STATIC_PAGES]
    dynamic = _dynamic_pages()
    if dynamic:
        out += ['', '## Страницы', '']
        out += [f'- [{title}]({base}{url})' for url, title, _ in dynamic]
    out.append('')
    return HttpResponse('\n'.join(out), content_type='text/plain; charset=utf-8')

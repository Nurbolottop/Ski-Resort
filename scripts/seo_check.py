"""SEO-проверка сайта: python3 scripts/seo_check.py [https://ski.baytur.kg]

Проверяет все страницы из sitemap.xml: уникальность и длину title/description,
один H1, alt у содержательных картинок, JSON-LD, а также robots.txt, sitemap и llms.txt.
Код выхода 1, если есть ошибки.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from html.parser import HTMLParser

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'https://ski.baytur.kg').rstrip('/')
UA = {'User-Agent': 'Mozilla/5.0 (compatible; SeoCheck/1.0)'}
errors, warnings = [], []


def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.meta, self.h1, self.imgs, self.ld, self.headings = '', {}, 0, [], [], []
        self._in_title = self._in_ld = False
        self._buf = ''

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'title':
            self._in_title = True
        elif tag == 'meta' and a.get('name'):
            self.meta[a['name']] = a.get('content', '')
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.headings.append(int(tag[1]))
            if tag == 'h1':
                self.h1 += 1
        elif tag == 'img':
            self.imgs.append(a)
        elif tag == 'script' and a.get('type') == 'application/ld+json':
            self._in_ld, self._buf = True, ''

    def handle_endtag(self, tag):
        if tag == 'title':
            self._in_title = False
        elif tag == 'script' and self._in_ld:
            self._in_ld = False
            self.ld.append(self._buf)

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self._buf += data


def ld_types(raw):
    data = json.loads(raw)
    return [str(i.get('@type')) for i in data.get('@graph', [data])]


def main():
    code, sitemap = fetch(BASE + '/sitemap.xml')
    if code != 200:
        errors.append(f'sitemap.xml: HTTP {code}')
        return
    urls = re.findall(r'<loc>([^<]+)</loc>', sitemap)
    blocks = re.findall(r'<url>(.*?)</url>', sitemap, re.S)
    no_lastmod = [re.search(r'<loc>([^<]+)', b).group(1) for b in blocks if '<lastmod>' not in b]
    if no_lastmod:
        errors.append(f'sitemap: нет lastmod у {len(no_lastmod)} URL')
    print(f'sitemap: {len(urls)} URL, картинок: {sitemap.count("<image:image>")}')

    titles, descs = Counter(), Counter()
    for url in urls:
        code, html = fetch(url)
        path = url.replace(BASE, '') or '/'
        if code != 200:
            errors.append(f'{path}: HTTP {code}')
            continue
        p = Page()
        p.feed(html)
        title, desc = p.title.strip(), p.meta.get('description', '').strip()
        titles[title] += 1
        descs[desc] += 1
        if not 10 <= len(title) <= 65:
            errors.append(f'{path}: title {len(title)} симв. «{title}»')
        if not 120 <= len(desc) <= 175:
            errors.append(f'{path}: description {len(desc)} симв.')
        if p.h1 != 1:
            errors.append(f'{path}: H1 = {p.h1}')
        skips = [(a, b) for a, b in zip(p.headings, p.headings[1:]) if b > a + 1]
        if skips:
            errors.append(f'{path}: пропуск уровня заголовков {skips[:3]}')
        if re.search(r'\{#|#\}|\{%|%\}', html):
            errors.append(f'{path}: на странице виден код шаблона')
        robots = p.meta.get('robots', '')
        if 'max-image-preview:large' not in robots:
            errors.append(f'{path}: нет meta robots max-image-preview:large')
        no_alt = [i.get('src', '')[-50:] for i in p.imgs
                  if not i.get('alt', '').strip() and i.get('role') != 'presentation' and 'aria-hidden' not in i]
        if no_alt:
            errors.append(f'{path}: {len(no_alt)} img без alt: {no_alt[:3]}')
        types = []
        for raw in p.ld:
            try:
                types += ld_types(raw)
            except ValueError as e:
                errors.append(f'{path}: JSON-LD не парсится: {e}')
        if path != '/' and 'BreadcrumbList' not in types:
            errors.append(f'{path}: нет BreadcrumbList')
        if path.startswith('/rooms/') and path != '/rooms/' and not any('HotelRoom' in t for t in types):
            errors.append(f'{path}: нет HotelRoom')
        if 'FAQPage' in types and 'faq' not in html:
            errors.append(f'{path}: FAQPage без видимых вопросов')
        print(f'{path:40} h1={p.h1} t={len(title):3} d={len(desc):3} img={len(p.imgs):2} ld={",".join(types)}')

    for t, n in titles.items():
        if n > 1:
            errors.append(f'title повторяется {n} раз: «{t}»')
    for d, n in descs.items():
        if n > 1:
            errors.append(f'description повторяется {n} раз: «{d[:60]}…»')

    code, robots = fetch(BASE + '/robots.txt')
    if code != 200 or 'Sitemap:' not in robots or 'Clean-param' not in robots:
        errors.append('robots.txt: нет Sitemap или Clean-param')
    if re.search(r'claude|anthropic', robots, re.I):
        errors.append('robots.txt: упоминание Claude/Anthropic')
    code, llms = fetch(BASE + '/llms.txt')
    if code != 200 or len(llms) < 2000:
        errors.append(f'llms.txt: HTTP {code}, {len(llms)} байт')
    code, html = fetch(BASE + '/no-such-page-xyz/')
    if code != 404 or 'noindex' not in html:
        errors.append(f'404: HTTP {code}, noindex={"noindex" in html}')


main()
for w in warnings:
    print('WARN', w)
for e in errors:
    print('FAIL', e)
print('OK' if not errors else f'{len(errors)} ошибок')
sys.exit(1 if errors else 0)

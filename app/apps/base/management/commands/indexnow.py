"""Отправка всех URL из sitemap.xml в IndexNow (Яндекс, Bing и др.): python manage.py indexnow"""
import json
import re
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand

from apps.base.seo import INDEXNOW_KEY

ENDPOINTS = ['https://api.indexnow.org/indexnow', 'https://yandex.com/indexnow']


class Command(BaseCommand):
    help = 'Отправить URL из sitemap.xml в IndexNow'

    def add_arguments(self, parser):
        parser.add_argument('--site', default='https://ski.baytur.kg')

    def handle(self, *args, **options):
        site = options['site'].rstrip('/')
        with urllib.request.urlopen(f'{site}/sitemap.xml', timeout=30) as r:
            urls = re.findall(r'<loc>([^<]+)</loc>', r.read().decode())
        payload = json.dumps({
            'host': site.split('://', 1)[1],
            'key': INDEXNOW_KEY,
            'keyLocation': f'{site}/{INDEXNOW_KEY}.txt',
            'urlList': urls,
        }).encode()
        for endpoint in ENDPOINTS:
            req = urllib.request.Request(endpoint, data=payload, method='POST',
                                         headers={'Content-Type': 'application/json; charset=utf-8'})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    self.stdout.write(f'{endpoint}: {r.status}, отправлено {len(urls)} URL')
            except urllib.error.HTTPError as e:
                self.stdout.write(f'{endpoint}: HTTP {e.code} {e.read().decode()[:200]}')
            except OSError as e:
                self.stdout.write(f'{endpoint}: нет ответа ({e}), повторите позже')

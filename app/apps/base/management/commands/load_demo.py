"""
Данные горнолыжной базы «Тоо-Ашуу» — только из официального Instagram @tooashuu.kg:
описание профиля и хайлайты «Прайс», «SKI PASS», «Прокат», «Меню», «Трансфер», «Трассы»,
«Контакты», «Отзывы», «Мы на карте», последние посты.

    python manage.py load_demo            # заполнить пустой сайт, существующее не трогать
    python manage.py load_demo --update   # обновить цены/меню/контакты по данным Instagram
                                          # и убрать устаревшие демо-записи

Фото загружаются отдельно: python manage.py import_photos <папка>.
"""
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.base.models import FAQ, Advantage, HeroSlide, Page, SiteSettings
from apps.cms.models import (
    GalleryAlbum, Lift, MenuCategory, MenuItem, Post, RentalItem, Review, Room, Service, ServiceCategory, SkiPass,
    Slope, TransferRoute,
)

# --------------------------------------------------------------------------------------------
# ДАННЫЕ ИЗ INSTAGRAM
# --------------------------------------------------------------------------------------------

SKI_PASSES = [
    # name, price, unit, note, featured
    ('Взрослый', 1500, '', '', True),
    ('На полдня', 950, '', '', False),
    ('Детский', 1000, '', 'С 6 до 12 лет', False),
    ('Разовый спуск', 500, '', 'Разовый спуск по канатной дороге', False),
]

RENTAL = [
    # category, name, description, price
    ('ski', 'Лыжный комплект', 'Лыжи, ботинки и палки', 1100),
    ('ski', 'Лыжи', '', 900),
    ('ski', 'Лыжные ботинки', '', 600),
    ('ski', 'Палки', '', 400),
    ('snowboard', 'Сноуборд комплект', 'Доска и ботинки', 1200),
    ('snowboard', 'Ботинки для сноуборда', '', 1000),
    ('clothes', 'Горнолыжные очки', '', 500),
    ('clothes', 'Перчатки', '', 500),
    ('other', 'Каримат', '', 200),
]

ROOMS = [
    # slug, name, guests, beds, price, unit, short, amenities
    ('cottage-2', 'Коттедж на двоих', 2, '2-местный', 8000, '',
     'Коттедж на 2 человек. В стоимость входят завтрак на двоих и 2 ски-пасса.',
     'Завтрак на двоих\n2 ски-пасса бесплатно'),
    ('cottage-3', 'Коттедж на троих', 3, '3-местный', 9500, '',
     'Коттедж на 3 человек. В стоимость входят завтрак на троих и 3 ски-пасса.',
     'Завтрак на троих\n3 ски-пасса бесплатно'),
    ('cottage-4', 'Коттедж на четверых', 4, '4-местный', 11500, '',
     'Коттедж на 4 человек. В стоимость входят завтрак на четверых и 4 ски-пасса.',
     'Завтрак на четверых\n4 ски-пасса бесплатно'),
    ('cottage-5', 'Коттедж на пятерых', 5, '5-местный', 13500, '',
     'Коттедж на 5 человек. В стоимость входят завтрак на пятерых и 5 ски-пассов.',
     'Завтрак на пятерых\n5 ски-пассов бесплатно'),
    ('wagon-8', 'Вагончик на 8 мест', 8, '8-местный', 8000, '', '8-местный вагончик.', ''),
    ('wagon-10', 'Вагончик на 10 мест', 10, '10-местный', 10000, '', '10-местный вагончик.', ''),
]
OLD_ROOM_SLUGS = ['standard', 'cottage', 'wagon']

MENU = {
    'Завтраки': [
        ('Каша овсяная', 260), ('Каша рисовая', 260), ('Яичница-глазунья из 2 яиц', 240),
        ('Сырники, 2 шт.', 260), ('Омлет с овощами', 300), ('Омлет с сыром и колбасой', 250), ('Хлеб', 90),
    ],
    'Супы': [
        ('Суп с фрикадельками', 320), ('Пельмени', 320), ('Том-ям с морепродуктами', 510), ('Борщ', 320),
        ('Солянка', 420), ('Чечевичный суп', 320), ('Шорпо из говядины', 420), ('Рамен с яйцом', 320),
    ],
    'Вторые блюда': [
        ('Куурдак из баранины', 880), ('Куурдак из говядины', 990), ('Лагман «гуйру»', 470),
        ('Лагман «босо»', 470), ('Жареная форель, 300 г', 660), ('Паста «Болоньезе»', 510),
        ('Феттучини с курицей и грибами', 570), ('Манты с мясом', 430),
    ],
    'Стейки': [('Рибай', 1500)],
    'Пицца': [('Маргарита', 540), ('Пепперони', 670), ('С курицей', 670)],
    'Салаты': [
        ('Цезарь с курицей', 495), ('Азиатский острый', 410), ('Греческий', 440), ('Свежий', 310),
        ('Оливье', 450), ('Шакарап', 310),
    ],
    'Закуски': [('Жареные луковые кольца', 275), ('Сосиски «Киндер»', 330), ('Куриные наггетсы', 330)],
    'Гарниры': [('Картофель фри', 220), ('Картофель по-деревенски', 220), ('Лимон', 90)],
    'Соусы': [
        ('Кетчуп', 50), ('Майонез', 70), ('Сметана', 70), ('Сырный', 70), ('Варенье', 70), ('Халапеньо', 100),
    ],
    'Банкетное меню': [('Плов «Лазер», 1 кг', 2950), ('Боорсок, 1 кг', 450)],
    'Горячие напитки': [
        ('Чай чёрный / зелёный', 120), ('Чай облепиховый', 300), ('Кофе 3 в 1', 50), ('Капучино', 210),
        ('Американо', 180), ('Латте', 210), ('Эспрессо', 180),
    ],
    'Безалкогольные напитки': [
        ('Coca-Cola, 1 л', 150), ('Сок J7', 240), ('Минеральная вода, 1 л', 80), ('Минеральная вода, 0,5 л', 60),
        ('Холодный чай Fuse Tea, 1 л', 150), ('Лимонад', 140), ('Энергетик «Нитро»', 130),
    ],
    'Пиво, вино, шампанское': [
        ('Пиво «Урбан», 1,35 л', 270), ('Пиво «Живое», 0,5 л', 210), ('Пиво «Арпа», 0,5 л', 220),
        ('Пиво Stella Artois, 0,5 л', 250), ('Пиво Heineken, 0,5 л', 240), ('Вино Baron', 900),
        ('Шампанское «Советское»', 950), ('Шампанское Bosca', 1200),
    ],
    'Снеки и сладости': [
        ('Арахис', 100), ('Вафли «Яшкино», 300 г', 90), ('Сыр «Чечил»', 180), ('Жвачка Dirol', 70),
        ('Mentos', 80), ('Семечки «Джин», 140 г', 120), ('Семечки «Джин», 100 г', 100),
        ('Семечки «Джин», 70 г', 80), ('Тералин', 95), ('Фисташки', 200), ("Чипсы Lay's", 140),
        ('Чипсы Pringles', 200), ('Шоколадный батончик', 120), ('Шоколад плиточный', 180),
    ],
}
OLD_MENU_CATEGORIES = ['Горячие блюда', 'Выпечка', 'Напитки']

SLOPES = [
    # name, level, length, drop, steepness, description
    ('Трасса 3 км', 'blue', 3000, None, 19, 'Длина 3 км, угол наклона 19°'),
    ('Трасса 2,8 км', 'red', 2800, None, 30, 'Длина 2 км 800 м, угол наклона 30°'),
    ('Трасса 2,6 км', 'black', 2600, None, 32, 'Длина 2 км 600 м, угол наклона 32°'),
]
OLD_SLOPES = [
    'Длинный спуск', 'Главный склон', 'Крутой склон', 'Фрирайд-зона',
    'Пологая трасса', 'Основная трасса', 'Крутая трасса',
]

TRANSFER = [
    ('Бишкек → Тоо-Ашуу', 'ТЦ «Дордой Плаза», Бишкек', '7:00 (или по договорённости)', '~2,5 часа', 1000,
     'Бус на 18 человек, водитель Владимир. Забронировать место можно по телефону 0558 616 133.'),
    ('Тоо-Ашуу → Бишкек', 'Горнолыжная база «Тоо-Ашуу»', '16:20', '~2,5 часа', 1000,
     'Бус на 18 человек, водитель Владимир.'),
]


# Ещё отзывы: комментарий гостьи в Instagram @tooashuu.kg (январь 2025) и отзыв о Baytur Resort & Spa
# (Иссык-Куль, та же сеть, resort.baytur.kg) — курорт указан в подписи.
EXTRA_REVIEWS = [
    ('Айчурек Темирбекова',
     'Крутое место: тихо, спокойно и очень удобно! А я наконец-то научилась нормально кататься на лыжах '
     'благодаря крутому инструктору Бахтияру — всё чётко объяснил. Рекомендую!', 400),
    ('Оксана Майбородова · Baytur Resort, Иссык-Куль',
     'В прошлом году отдыхали командой сотрудников почти 10 дней. Понравилась атмосфера, сервис очень тёплый. '
     'Так красиво и эстетично подошли к оформлению, где каждый уголок оформлен с любовью. Рекомендую.', 401),
]

INSTRUCTOR_TEXT = (
    'Обучение катанию на лыжах или сноуборде. Объяснение правильной стойки и техники. '
    'Обучение торможению и поворотам. Практика спуска под контролем инструктора. '
    'Обучение правилам безопасности на склоне.'
)


class Command(BaseCommand):
    help = 'Данные «Тоо-Ашуу» из Instagram. --update — обновить существующие записи.'

    def add_arguments(self, parser):
        parser.add_argument('--update', action='store_true', help='Перезаписать данные по Instagram')

    @transaction.atomic
    def handle(self, *args, update=False, **options):
        self.update = update
        self.settings()
        self.home()
        self.slopes()
        self.ski_passes()
        self.rental()
        self.rooms()
        self.services()
        self.menu()
        self.transfer()
        self.reviews()
        self.gallery()
        self.faq()
        self.posts()
        self.pages()
        self.stdout.write(self.style.SUCCESS('Данные «Тоо-Ашуу» загружены.'))

    def upsert(self, model, lookup, values):
        """get_or_create, а с --update — update_or_create."""
        if self.update:
            return model.objects.update_or_create(defaults=values, **lookup)
        return model.objects.get_or_create(defaults=values, **lookup)

    # ------------------------------------------------------------------------------------------

    def settings(self):
        site = SiteSettings.load()
        if site.whatsapp and not self.update:
            return
        site.name = 'Тоо-Ашуу'
        site.full_name = 'Горнолыжная база «Тоо-Ашуу»'
        site.tagline = 'Горнолыжная база на высоте 3 000 метров — в 120 км от Бишкека по трассе Бишкек — Ош.'
        site.season = ''
        site.open_weekdays = '5,6'  # «ГРАФИК РАБОТЫ: суббота и воскресенье»
        site.lift_hours = ''
        # Последний пост (18.03.2026): «Сезон закрыт… До скорой встречи в новом сезоне!»
        site.is_season_open = False
        site.whatsapp = '+996 701 797 480'
        site.phone = '+996 555 444 242'
        site.phone_2 = '+996 770 797 370'
        site.email = 'pr@baytur.kg'
        site.transfer_contact = 'Владимир'
        site.transfer_phone = '+996 558 616 133'
        site.address = 'Перевал Тоо-Ашуу, трасса Бишкек — Ош'
        site.working_hours = (
            'Отдел бронирования (WhatsApp): +996 701 797 480\n'
            'Администратор базы: +996 555 444 242, WhatsApp +996 770 797 370\n'
            'Жалобы и предложения: pr@baytur.kg'
        )
        site.instagram = 'https://www.instagram.com/tooashuu.kg/'
        # Точка «Горнолыжная база Тоо Ашуу» с карты из хайлайта «Мы на карте» — для погоды
        site.latitude = site.latitude or Decimal('42.333000')
        site.longitude = site.longitude or Decimal('73.817000')
        site.altitude_base = None
        site.altitude_top = 3000
        site.distance_km = 120
        # Карта — по названию точки из хайлайта «Мы на карте»
        site.map_embed_url = (
            'https://www.google.com/maps?q=%D0%93%D0%BE%D1%80%D0%BD%D0%BE%D0%BB%D1%8B%D0%B6%D0%BD%D0%B0%D1%8F'
            '+%D0%B1%D0%B0%D0%B7%D0%B0+%D0%A2%D0%BE%D0%BE+%D0%90%D1%88%D1%83%D1%83&z=11&output=embed'
        )
        site.directions = (
            '<p><strong>На машине.</strong> База находится в 120 км от черты Бишкека — '
            'около 2,5 часов езды на автотранспорте по трассе Бишкек — Ош.</p>'
            '<p><strong>Трансфер.</strong> По выходным ходит бус на 18 человек: сбор у ТЦ «Дордой Плаза» в 7:00, '
            'обратно с базы в 16:20. Стоимость — 1 000 сом с человека. Бронирование места — '
            'у водителя Владимира: 0558 616 133.</p>'
        )
        site.save()

    def home(self):
        slides = [
            ('Перевал Тоо-Ашуу · 3 000 м', 'Снег выше облаков',
             'Горнолыжная база в 120 км от Бишкека — каждые выходные сезона.'),
            ('Три трассы · до 3 км', 'Выходные на склоне',
             'Три трассы разного уровня сложности и канатная дорога.'),
            ('Коттеджи · кафе · трансфер', 'Приезжайте налегке',
             'Коттеджи с завтраком и ски-пассами, прокат, кафе и трансфер из Бишкека.'),
        ]
        for i, (eyebrow, title, text) in enumerate(slides):
            self.upsert(HeroSlide, {'title': title}, {'eyebrow': eyebrow, 'text': text, 'order': i})
        if self.update:
            HeroSlide.objects.filter(title__in=['Ski Resort', 'Снег, горы и свобода', 'Ski-in / Ski-out']).delete()

        advantages = [
            ('mountain', 'Высота 3 000 метров', 'База на высоте 3 000 метров над уровнем моря, в 120 км от Бишкека.'),
            ('ski', 'Три трассы', 'Длиной 2,6, 2,8 и 3 км — от пологой до крутой, на 32 градуса.'),
            ('home', 'Коттеджи с завтраком', 'В стоимость коттеджа входят завтрак и ски-пассы на всех гостей.'),
            ('car', 'Трансфер из Бишкека', 'Бус на 18 мест по выходным — 1 000 сом с человека.'),
        ]
        for i, (icon, title, text) in enumerate(advantages):
            self.upsert(Advantage, {'order': i}, {'icon': icon, 'title': title, 'text': text})

    def slopes(self):
        for i, (name, level, length, drop, steep, desc) in enumerate(SLOPES):
            self.upsert(Slope, {'name': name}, {
                'level': level, 'length_m': length, 'vertical_drop_m': drop, 'steepness': steep,
                'description': desc, 'order': i,
            })
        if self.update:
            Slope.objects.filter(name__in=OLD_SLOPES).delete()

        self.upsert(Lift, {'order': 0}, {
            'name': 'Канатная дорога', 'lift_type': 'chair', 'ride_minutes': None, 'hours': '',
        })
        if self.update:
            Lift.objects.exclude(order=0).delete()

    def ski_passes(self):
        for i, (name, price, unit, note, featured) in enumerate(SKI_PASSES):
            self.upsert(SkiPass, {'name': name}, {
                'price': price, 'price_unit': unit, 'note': note, 'is_featured': featured, 'order': i,
                'features': '',
            })
        if self.update:
            SkiPass.objects.filter(name='Студенческий').delete()

    def rental(self):
        for i, (category, name, desc, price) in enumerate(RENTAL):
            self.upsert(RentalItem, {'name': name}, {
                'category': category, 'description': desc, 'price_day': price, 'price_hour': None, 'order': i,
            })
        if self.update:
            RentalItem.objects.filter(
                name__in=['Комплект горных лыж', 'Комплект сноуборда', 'Горнолыжный костюм', 'Санки'],
            ).delete()

    def rooms(self):
        for i, (slug, name, guests, beds, price, unit, short, amenities) in enumerate(ROOMS):
            self.upsert(Room, {'slug': slug}, {
                'name': name, 'max_guests': guests, 'beds': beds, 'price_from': price, 'price_unit': unit,
                'short_description': short, 'amenities': amenities, 'order': i,
                'description': f'<p>{short}</p>',
            })
        if self.update:
            Room.objects.filter(slug__in=OLD_ROOM_SLUGS).delete()

    def services(self):
        category, _ = self.upsert(ServiceCategory, {'slug': 'instructors'}, {'name': 'Инструкторы', 'order': 0})
        if self.update:
            category.services.all().delete()
        if not category.services.exists():
            Service.objects.create(
                category=category, name='Услуги инструктора', price='2 000 сом',
                description=INSTRUCTOR_TEXT,
            )

    def menu(self):
        if self.update:
            MenuCategory.objects.filter(name__in=OLD_MENU_CATEGORIES).delete()
        for i, (name, items) in enumerate(MENU.items()):
            category, created = self.upsert(MenuCategory, {'name': name}, {'order': i})
            if created or self.update:
                category.items.all().delete()
                MenuItem.objects.bulk_create([
                    MenuItem(category=category, name=item, price=price, order=j)
                    for j, (item, price) in enumerate(items)
                ])

    def transfer(self):
        for i, (name, point, schedule, duration, price, desc) in enumerate(TRANSFER):
            self.upsert(TransferRoute, {'name': name}, {
                'departure_point': point, 'schedule': schedule, 'duration': duration, 'price': price,
                'price_unit': 'человека', 'description': desc, 'order': i,
            })

    def reviews(self):
        self.upsert(Review, {'name': 'Ядвига и Кшиштоф Бербека, Краков'}, {
            'rating': 5, 'is_published': True,
            'text': 'Большое спасибо менеджеру и всей команде, работающей в Тоо-Ашуу. Мы провели Новый год '
                    'там в третий раз — и мы вернёмся снова. Большое спасибо за тёплый приём, мы ценим '
                    'большие усилия и тяжёлую работу в этот период. Привет из Кракова!',
        })
        for name, text, days in EXTRA_REVIEWS:
            obj, _ = self.upsert(Review, {'name': name}, {'rating': 5, 'is_published': True, 'text': text})
            Review.objects.filter(pk=obj.pk).update(created_at=timezone.now() - timedelta(days=days))

    def gallery(self):
        albums = [('Горы', 'mountains'), ('Катание', 'skiing'), ('Подъёмники', 'lifts'), ('Отдых', 'rest')]
        for i, (title, slug) in enumerate(albums):
            self.upsert(GalleryAlbum, {'slug': slug}, {'title': title, 'order': i})
        if self.update:
            GalleryAlbum.objects.filter(slug__startswith='season-').delete()

    def faq(self):
        items = [
            ('Когда работает база?',
             '<p>График работы — суббота и воскресенье. Бронирование — WhatsApp +996 701 797 480.</p>'),
            ('Как добраться?',
             '<p>120 км от черты Бишкека, около 2,5 часов по трассе Бишкек — Ош. Есть трансфер: '
             'бус на 18 человек от ТЦ «Дордой Плаза» в 7:00, 1 000 сом с человека.</p>'),
            ('Сколько стоит ски-пасс?',
             '<p>Взрослый — 1 500 сом, на полдня — 950 сом, детский (6–12 лет) — 1 000 сом, '
             'разовый спуск по канатной дороге — 500 сом.</p>'),
            ('Что входит в проживание?',
             '<p>В коттеджах завтрак и ски-пассы для всех гостей уже включены в стоимость: '
             'например, в 2-местном коттедже за 8 000 сом — завтрак на двоих и 2 ски-пасса.</p>'),
            ('Можно ли взять снаряжение в прокат?',
             '<p>Да: лыжный комплект — 1 100 сом, сноуборд комплект — 1 200 сом, а также очки, перчатки '
             'и отдельные позиции. Полный прайс — в разделе «Прокат».</p>'),
            ('Есть ли инструкторы?', '<p>Да, услуги инструктора — 2 000 сом.</p>'),
        ]
        if self.update:
            FAQ.objects.filter(question='Что взять с собой?').delete()
        for i, (question, answer) in enumerate(items):
            self.upsert(FAQ, {'question': question}, {'answer': answer, 'order': i})

    def posts(self):
        self.upsert(Post, {'slug': 'season-closed-2026'}, {
            'title': 'Сезон закрыт',
            'excerpt': 'Спасибо каждому из вас за эту зиму — за радость, смех, яркие эмоции и любовь к горам.',
            'content': '<p>Спасибо каждому из вас за эту зиму — за радость, смех, яркие эмоции и любовь к горам.</p>'
                       '<p>Вы сделали этот сезон по-настоящему особенным для нас.</p>'
                       '<p><strong>До скорой встречи в новом сезоне!</strong></p>',
            'published_at': datetime(2026, 3, 18, 6, 44, tzinfo=dt_timezone.utc),
        })
        Post.objects.get_or_create(slug='new-website', defaults={
            'title': 'У базы «Тоо-Ашуу» новый сайт',
            'excerpt': 'Цены, меню, прокат, трансфер и погода на перевале — теперь в одном месте.',
            'content': '<p>На сайте собрано всё, что нужно перед поездкой: цены на ски-пассы, прокат '
                       'и проживание, меню кафе, расписание трансфера и прогноз погоды на перевале.</p>'
                       '<p>Оставить заявку можно прямо на сайте или написать в WhatsApp +996 701 797 480.</p>',
        })

    def pages(self):
        about = (
            '<p>«Тоо-Ашуу» — горнолыжная база на перевале Тоо-Ашуу, в 120 км от черты Бишкека: '
            'около 2,5 часов езды по трассе Бишкек — Ош. База находится на высоте 3 000 метров над уровнем моря.</p>'
            '<p>База оборудована тремя трассами различного уровня сложности и протяжённости. '
            'Работает канатная дорога.</p>'
            '<p>Для гостей — коттеджи (с завтраком и ски-пассами) и вагончики, кафе, прокат снаряжения, '
            'инструкторы и трансфер из Бишкека. График работы — суббота и воскресенье.</p>'
        )
        pages = [
            ('О базе', 'about', about),
            ('Политика конфиденциальности', 'privacy',
             '<p>Мы используем имя, телефон и e-mail из форм на сайте только для обработки заявок '
             'и связи с вами. Данные не передаются третьим лицам.</p>'),
            ('Публичная оферта', 'offer', '<p>Текст публичной оферты будет опубликован позже.</p>'),
            ('Авторы фото', 'photo-credits',
             (Path(__file__).with_name('photo_credits.html')).read_text(encoding='utf-8')),
        ]
        for title, slug, content in pages:
            if slug in ('about', 'photo-credits'):
                self.upsert(Page, {'slug': slug}, {'title': title, 'content': content})
            else:
                Page.objects.get_or_create(slug=slug, defaults={'title': title, 'content': content})

"""
Стартовое наполнение сайта данными горнолыжной базы «Тоо-Ашуу».

Источники: профиль @tooashuu.kg, 24.kg (январь 2024), adrenalinicsilence.kz,
nomadsland.travel. Цены — по публикациям прошлых сезонов: перед запуском
сверьте их с актуальным прайсом в админке.

Повторный запуск безопасен: существующие записи не перезаписываются.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.base.models import FAQ, Advantage, HeroSlide, Page, SiteSettings
from apps.cms.models import (
    GalleryAlbum, Lift, MenuCategory, MenuItem, Post, RentalItem, Room, Service, ServiceCategory, SkiPass, Slope,
    TransferRoute,
)


class Command(BaseCommand):
    help = 'Заполняет сайт стартовыми данными базы «Тоо-Ашуу» (существующие записи не трогает).'

    @transaction.atomic
    def handle(self, *args, **options):
        self.settings()
        self.home()
        self.slopes()
        self.ski_passes()
        self.rental()
        self.rooms()
        self.services()
        self.menu()
        self.transfer()
        self.gallery()
        self.faq()
        self.posts()
        self.pages()
        self.stdout.write(self.style.SUCCESS('Данные «Тоо-Ашуу» загружены. Проверьте цены в админке.'))

    def settings(self):
        site = SiteSettings.load()
        if site.whatsapp:
            return
        site.name = 'Тоо-Ашуу'
        site.full_name = 'Горнолыжная база «Тоо-Ашуу»'
        site.tagline = 'Горнолыжная база на перевале Тоо-Ашуу — почти 3 000 метров, солнце и снег больше метра всю зиму.'
        site.season = 'Сезон 2026/2027'
        site.open_weekdays = '5,6'
        site.lift_hours = '9:30 – 16:30'
        site.whatsapp = '+996 701 797 480'
        site.transfer_contact = 'Владимир'
        site.transfer_phone = '+996 558 616 133'
        site.address = 'Чуйская область, перевал Тоо-Ашуу, трасса Бишкек — Ош'
        site.working_hours = (
            'Подъёмники: 9:30 – 16:30\n'
            'Суббота и воскресенье\n'
            'Перед поездкой уточняйте состояние дороги через перевал'
        )
        site.instagram = 'https://www.instagram.com/tooashuu.kg/'
        site.latitude = Decimal('42.333000')
        site.longitude = Decimal('73.817000')
        site.altitude_base = 2520
        site.altitude_top = 3000
        site.distance_km = 120
        site.directions = (
            '<p><strong>На машине.</strong> Из Бишкека — по трассе Бишкек — Ош через Кара-Балтинское ущелье '
            'до перевала Тоо-Ашуу, около 120 км и 2,5–3 часа в пути. База находится на южной стороне перевала, '
            'у въезда в Суусамырскую долину, сразу за тоннелем.</p>'
            '<p><strong>Зимой</strong> обязательна зимняя резина; на перевале бывают снегопады и ограничения движения — '
            'проверьте статус дороги перед выездом.</p>'
            '<p><strong>Трансфер.</strong> По выходным из Бишкека возит Владимир — бронируйте место заранее.</p>'
        )
        site.save()

    def home(self):
        slides = [
            ('Перевал Тоо-Ашуу · 3 000 м', 'Снег выше облаков',
             'Горнолыжная база в 120 км от Бишкека — каждые выходные сезона.'),
            ('Суббота и воскресенье', 'Выходные на склоне',
             'Кресельный подъёмник, широкие трассы и фрирайд по свежему снегу.'),
            ('Прокат · кафе · трансфер', 'Приезжайте налегке',
             'Снаряжение, горячая еда и трансфер из Бишкека — всё на месте.'),
        ]
        for i, (eyebrow, title, text) in enumerate(slides):
            HeroSlide.objects.get_or_create(title=title, defaults={'eyebrow': eyebrow, 'text': text, 'order': i})

        advantages = [
            ('mountain', 'Почти 3 000 метров',
             'Высокогорье и южный солнечный склон: снег лежит больше метра всю зиму.'),
            ('lift', 'Кресельный подъёмник',
             'Подъём наверх около 17 минут, а для начинающих — бугель.'),
            ('ski', 'Трассы и фрирайд',
             'Широкий склон для новичков и целина вокруг — для любителей пухляка.'),
            ('car', 'Трансфер из Бишкека',
             'По выходным возим гостей до базы и обратно — бронируйте место заранее.'),
        ]
        for i, (icon, title, text) in enumerate(advantages):
            Advantage.objects.get_or_create(title=title, defaults={'icon': icon, 'text': text, 'order': i})

    def slopes(self):
        slopes = [
            ('Длинный спуск', 'green', 3000, None, 19, 'Пологая трасса — подходит для новичков'),
            ('Главный склон', 'blue', 2800, 700, 30, 'Основная трасса вдоль кресельного подъёмника'),
            ('Крутой склон', 'red', 2600, None, 32, 'Для уверенно катающихся'),
            ('Фрирайд-зона', 'freeride', None, None, None, 'Целина вокруг трасс — только с опытом и лавинным снаряжением'),
        ]
        for i, (name, level, length, drop, steep, desc) in enumerate(slopes):
            Slope.objects.get_or_create(name=name, defaults={
                'level': level, 'length_m': length, 'vertical_drop_m': drop, 'steepness': steep,
                'description': desc, 'order': i,
            })

        lifts = [
            ('Кресельный подъёмник', 'chair', 17),
            ('Бугельный подъёмник', 'drag', None),
        ]
        for i, (name, lift_type, minutes) in enumerate(lifts):
            Lift.objects.get_or_create(name=name, defaults={
                'lift_type': lift_type, 'ride_minutes': minutes, 'hours': '9:30 – 16:30', 'order': i,
            })

    def ski_passes(self):
        passes = [
            ('Взрослый', 1200, '', True),
            ('Студенческий', 1000, 'При предъявлении студенческого билета', False),
            ('Детский', 890, 'Дети до 6 лет катаются бесплатно', False),
        ]
        for i, (name, price, note, featured) in enumerate(passes):
            SkiPass.objects.get_or_create(name=name, defaults={
                'price': price, 'price_unit': 'день', 'note': note, 'is_featured': featured, 'order': i,
                'features': 'Все подъёмники\nС 9:30 до 16:30',
            })

    def rental(self):
        items = [
            ('ski', 'Комплект горных лыж', 'Лыжи, ботинки, палки', 600),
            ('snowboard', 'Комплект сноуборда', 'Доска и ботинки', 700),
            ('clothes', 'Горнолыжный костюм', 'Куртка и штаны', None),
            ('kids', 'Санки', '', 300),
        ]
        for i, (category, name, desc, price) in enumerate(items):
            RentalItem.objects.get_or_create(name=name, defaults={
                'category': category, 'description': desc, 'price_day': price, 'order': i,
            })

    def rooms(self):
        rooms = [
            ('Номер в гостинице', 'standard', 2, '2 кровати', 6500, 'ночь',
             'Тёплый номер на базе на высоте почти 3 000 м — утром сразу на склон.'),
            ('Домик', 'cottage', 6, 'Несколько спален', 11900, 'ночь',
             'Отдельный домик для семьи или компании прямо у трассы.'),
            ('Вагончик', 'wagon', 10, 'Общие спальные места', 700, 'место',
             'Бюджетный вариант для компании: до 10 человек, оплата за место.'),
        ]
        for i, (name, slug, guests, beds, price, unit, short) in enumerate(rooms):
            Room.objects.get_or_create(slug=slug, defaults={
                'name': name, 'max_guests': guests, 'beds': beds, 'price_from': price, 'price_unit': unit,
                'short_description': short, 'order': i,
                'amenities': 'Отопление\nКафе на базе\nХранение лыж\nВид на горы',
                'description': f'<p>{short}</p><p>Наша база устроена «наоборот»: жильё стоит наверху, '
                               'поэтому утром не нужно ждать подъёмника — выходите и катите вниз.</p>',
            })

    def services(self):
        category, created = ServiceCategory.objects.get_or_create(
            slug='instructors', defaults={'name': 'Инструкторы', 'order': 0},
        )
        if created:
            services = [
                ('Индивидуальное занятие', 'Горные лыжи или сноуборд, для любого уровня', '1 000 сом / час'),
                ('Занятие для детей', 'Спокойный темп и игровая форма', 'по запросу'),
            ]
            for j, (name, desc, price) in enumerate(services):
                Service.objects.create(category=category, name=name, description=desc, price=price, order=j)

    def menu(self):
        menu = {
            'Горячие блюда': [
                ('Лагман', 'Домашняя лапша, говядина, овощи', '350 г', 450, True),
                ('Плов', 'Рис, говядина, морковь', '300 г', 450, False),
                ('Манты', 'С мясом и луком, 5 шт.', '300 г', 400, False),
                ('Шорпо', 'Наваристый суп', '400 мл', 400, False),
            ],
            'Выпечка': [
                ('Самса', 'С мясом', '1 шт.', 120, True),
                ('Боорсоки', 'С вареньем', '150 г', 150, False),
            ],
            'Напитки': [
                ('Чай травяной', 'Чабрец, шиповник', '0,5 л', 100, False),
                ('Кофе', '', '0,25 л', 150, False),
                ('Глинтвейн безалкогольный', 'Вишнёвый сок и специи', '0,3 л', 200, True),
            ],
        }
        for i, (name, items) in enumerate(menu.items()):
            category, created = MenuCategory.objects.get_or_create(name=name, defaults={'order': i})
            if created:
                for j, (item, desc, weight, price, hit) in enumerate(items):
                    MenuItem.objects.create(
                        category=category, name=item, description=desc, weight=weight,
                        price=price, is_hit=hit, order=j,
                    )

    def transfer(self):
        routes = [
            ('Бишкек → Тоо-Ашуу', 'Бишкек, место встречи — по договорённости',
             'Сб и вс утром — время уточняйте у Владимира', '2,5–3 часа'),
            ('Тоо-Ашуу → Бишкек', 'База Тоо-Ашуу', 'Сб и вс после закрытия подъёмников', '2,5–3 часа'),
        ]
        for i, (name, point, schedule, duration) in enumerate(routes):
            TransferRoute.objects.get_or_create(name=name, defaults={
                'departure_point': point, 'schedule': schedule, 'duration': duration, 'order': i,
            })

    def gallery(self):
        albums = [
            ('Сезон 2025–2026', 'season-2025-2026'),
            ('Сезон 2024–2025', 'season-2024-2025'),
            ('Сезон 2023–2024', 'season-2023-2024'),
        ]
        for i, (title, slug) in enumerate(albums):
            GalleryAlbum.objects.get_or_create(slug=slug, defaults={'title': title, 'order': i})

    def faq(self):
        items = [
            ('Когда работает база?',
             '<p>По субботам и воскресеньям, подъёмники — с 9:30 до 16:30. '
             'Перед поездкой уточните статус в WhatsApp: погода на перевале меняется быстро.</p>'),
            ('Как добраться?',
             '<p>Около 120 км от Бишкека по трассе Бишкек — Ош, 2,5–3 часа в пути. '
             'Можно доехать на своей машине (обязательно зимняя резина) или трансфером — '
             'подробности на странице «Трансфер».</p>'),
            ('Сколько стоит ски-пасс?',
             '<p>Взрослый — 1 200 сом, студенческий — 1 000 сом, детский — 890 сом. '
             'Дети до 6 лет катаются бесплатно. Актуальные цены — в разделе «Цены».</p>'),
            ('Можно ли взять снаряжение в прокат?',
             '<p>Да: лыжи, сноуборды, костюмы и санки. В выходные спрос высокий — '
             'лучше написать заранее, чтобы мы подготовили комплект.</p>'),
            ('Что взять с собой?',
             '<p>Солнцезащитные очки и крем — на высоте 3 000 м солнце очень активное, '
             'тёплую одежду, перчатки и документы.</p>'),
        ]
        for i, (question, answer) in enumerate(items):
            FAQ.objects.get_or_create(question=question, defaults={'answer': answer, 'order': i})

    def posts(self):
        Post.objects.get_or_create(slug='new-website', defaults={
            'title': 'У базы «Тоо-Ашуу» новый сайт',
            'excerpt': 'Состояние склона, погода на перевале, цены, прокат и трансфер — теперь в одном месте.',
            'content': '<p>Мы запустили сайт, где собрали всё, что нужно перед поездкой: статус базы на сегодня, '
                       'прогноз погоды на перевале, цены на ски-пассы и прокат, меню кафе и расписание трансфера.</p>'
                       '<p>Оставить заявку на проживание можно прямо на сайте или написать нам в WhatsApp.</p>',
        })

    def pages(self):
        pages = [
            ('О базе', 'about',
             '<p>«Тоо-Ашуу» — горнолыжная база на южном склоне одноимённого перевала, у въезда в Суусамырскую '
             'долину, в 120 км от Бишкека. Высота — от 2 500 до 3 000 метров над уровнем моря.</p>'
             '<p>Благодаря высоте снег здесь лежит больше метра всю зиму, а южная экспозиция дарит солнце '
             'с утра до вечера. С верхней точки открывается панорама на горы и Суусамырскую долину.</p>'
             '<p>База устроена «наоборот»: жильё и кафе находятся наверху, поэтому утро начинается со спуска. '
             'На склоне работают кресельный и бугельный подъёмники, рядом — широкие трассы для новичков '
             'и целина для любителей фрирайда.</p>'
             '<p>Мы работаем по субботам и воскресеньям. Есть прокат, кафе с домашней кухней и трансфер из Бишкека.</p>'),
            ('Политика конфиденциальности', 'privacy',
             '<p>Мы используем имя, телефон и e-mail из форм на сайте только для обработки заявок '
             'и связи с вами. Данные не передаются третьим лицам.</p>'),
            ('Публичная оферта', 'offer', '<p>Текст публичной оферты будет опубликован позже.</p>'),
        ]
        for title, slug, content in pages:
            Page.objects.get_or_create(slug=slug, defaults={'title': title, 'content': content})

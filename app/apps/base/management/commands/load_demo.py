from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.base.models import Advantage, HeroSlide, Page, SiteSettings
from apps.cms.models import (
    Lift, MenuCategory, MenuItem, Offer, Post, Review, Room, Service, ServiceCategory, SkiPass, Slope, TransferRoute,
)


class Command(BaseCommand):
    help = 'Заполняет сайт демо-контентом. Существующие записи (по slug/названию) не перезаписываются.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.settings()
        self.home()
        self.slopes()
        self.ski_passes()
        self.rooms()
        self.services()
        self.menu()
        self.transfer()
        self.offers()
        self.reviews()
        self.posts()
        self.pages()
        self.stdout.write(self.style.SUCCESS('Демо-данные загружены.'))

    def settings(self):
        site = SiteSettings.load()
        if not site.phone:
            site.tagline = 'Зимний отдых вашей мечты в горах'
            site.season = 'Сезон 2026/2027'
            site.phone = '+996 555 000 000'
            site.phone_2 = '+996 700 000 000'
            site.email = 'info@example.com'
            site.address = 'Адрес курорта'
            site.working_hours = 'Подъёмники: 9:00 – 17:00\nПрокат: 8:30 – 18:00\nЕжедневно в сезон'
            site.whatsapp = '996555000000'
            site.temperature = -6
            site.snow_depth = 85
            site.save()
        if not site.transfer_phone:
            site.instagram = site.instagram or 'https://www.instagram.com/'
            site.transfer_contact = 'Диспетчер трансфера'
            site.transfer_phone = '+996 555 111 111'
            site.directions = (
                '<p><strong>На автомобиле.</strong> Из Бишкека по трассе на юг, около 2,5 часов в пути. '
                'Зимой обязательна зимняя резина, на перевале возможны цепи.</p>'
                '<p><strong>Парковка</strong> у нижней станции подъёмника — бесплатно для гостей.</p>'
                '<p><strong>Трансфер.</strong> По выходным курсирует микроавтобус — расписание выше.</p>'
            )
            site.save()

    def home(self):
        slides = [
            ('Горнолыжный курорт · Сезон 2026/2027', 'Ski Resort'),
            ('14 трасс · 5 подъёмников', 'Снег, горы и свобода'),
            ('Отель и коттеджи у склона', 'Ski-in / Ski-out'),
        ]
        for i, (eyebrow, title) in enumerate(slides):
            HeroSlide.objects.get_or_create(title=title, defaults={'eyebrow': eyebrow, 'order': i})

        advantages = [
            ('Трассы и подъёмники', '14 трасс всех уровней сложности, кресельные и бугельные подъёмники, ночное катание.'),
            ('Прокат и школа', 'Лыжи, сноуборды и экипировка. Инструкторы для детей и взрослых.'),
            ('Отель и коттеджи', 'Номера разных категорий и коттеджи в шаговой доступности от склона.'),
            ('Рестораны и SPA', 'Кафе на склоне, ресторан, сауны и бассейн для отдыха после катания.'),
        ]
        for i, (title, text) in enumerate(advantages):
            Advantage.objects.get_or_create(title=title, defaults={'text': text, 'order': i})

    def slopes(self):
        slopes = [
            ('Учебная', 'green', 400, 40, 'Учебная зона с траволатором'),
            ('Солнечная', 'green', 1200, 150, ''),
            ('Семейная', 'green', 1600, 200, ''),
            ('Лесная', 'blue', 2100, 320, 'Проходит через еловый лес'),
            ('Панорама', 'blue', 2500, 380, 'Виды на всю долину'),
            ('Бульвар', 'blue', 1800, 260, ''),
            ('Красная стрела', 'red', 2300, 480, ''),
            ('Вираж', 'red', 1900, 420, 'Серия крутых поворотов'),
            ('Чёрный кулуар', 'black', 1400, 520, 'Только для опытных'),
            ('Фрирайд-зона', 'black', 1600, 600, 'Вне подготовленных трасс, с гидом'),
        ]
        for i, (name, level, length, drop, desc) in enumerate(slopes):
            Slope.objects.get_or_create(name=name, defaults={
                'level': level, 'length_m': length, 'vertical_drop_m': drop,
                'description': desc, 'order': i, 'is_open': name != 'Фрирайд-зона',
            })

        lifts = [
            ('Гондола «Вершина»', 'gondola', 3200, 2400, '9:00 – 16:30'),
            ('Кресельный №1', 'chair', 1800, 1800, '9:00 – 17:00'),
            ('Кресельный №2', 'chair', 1500, 1500, '9:00 – 17:00'),
            ('Бугель «Учебный»', 'drag', 450, 900, '9:00 – 17:00'),
            ('Траволатор', 'carpet', 120, 600, '9:00 – 17:00'),
        ]
        for i, (name, lift_type, length, capacity, hours) in enumerate(lifts):
            Lift.objects.get_or_create(name=name, defaults={
                'lift_type': lift_type, 'length_m': length, 'capacity': capacity, 'hours': hours, 'order': i,
            })

    def ski_passes(self):
        passes = [
            ('Полдня', 1500, 1000, 'С 13:00 до 17:00\nВсе подъёмники', False),
            ('Весь день', 2500, 1700, 'С 9:00 до 17:00\nВсе подъёмники\nНочное катание по пятницам', True),
            ('3 дня', 6500, 4500, 'Три любых дня в течение недели\nВсе подъёмники', False),
            ('Сезонный', 35000, 22000, 'Весь сезон без ограничений\nСкидка 10% на прокат', False),
        ]
        for i, (name, price, child, features, featured) in enumerate(passes):
            SkiPass.objects.get_or_create(name=name, defaults={
                'price': price, 'price_child': child, 'features': features, 'is_featured': featured, 'order': i,
            })

    def rooms(self):
        amenities = 'Wi-Fi\nТелевизор\nСейф\nФен\nСушилка для обуви\nХранение лыж'
        rooms = [
            ('Стандарт', 'standard', 2, '1 Queen-size / 2 Twin', 22, 8000,
             'Уютный номер с видом на горы. Завтрак и хранение снаряжения включены.'),
            ('Делюкс', 'deluxe', 3, '1 King-size + диван', 32, 12000,
             'Просторный номер с балконом и панорамным видом на склон.'),
            ('Семейный', 'family', 4, '1 King-size + 2 Twin', 45, 16000,
             'Две комнаты для семьи с детьми, детская кроватка по запросу.'),
            ('Коттедж', 'cottage', 6, '3 спальни', 90, 25000,
             'Деревянный коттедж с камином, кухней и террасой для семьи или компании.'),
        ]
        for i, (name, slug, guests, beds, area, price, short) in enumerate(rooms):
            Room.objects.get_or_create(slug=slug, defaults={
                'name': name, 'max_guests': guests, 'beds': beds, 'area': area, 'price_from': price,
                'short_description': short, 'amenities': amenities, 'order': i,
                'description': f'<p>{short}</p><p>В стоимость входит завтрак «шведский стол», '
                               'посещение бассейна и бесплатный трансфер до нижней станции подъёмника.</p>',
            })

    def services(self):
        categories = {
            ('Прокат снаряжения', 'rental'): [
                ('Комплект горных лыж', 'Лыжи, ботинки, палки', 'от 1 500 сом / день'),
                ('Комплект сноуборда', 'Сноуборд и ботинки', 'от 1 500 сом / день'),
                ('Шлем и маска', '', '500 сом / день'),
                ('Сервис', 'Заточка кантов, парафин, ремонт скользяка', 'от 800 сом'),
            ],
            ('Школа катания', 'school'): [
                ('Индивидуальное занятие', 'Инструктор по лыжам или сноуборду', '3 000 сом / час'),
                ('Групповое занятие', 'Группы до 6 человек', '1 500 сом / час'),
                ('Детская школа', 'Для детей от 4 лет, игровая форма', '2 000 сом / час'),
            ],
            ('Рестораны и бары', 'restaurants'): [
                ('Ресторан «Вершина»', 'Европейская и национальная кухня', ''),
                ('Кафе на склоне', 'Горячие напитки, супы, выпечка', ''),
                ('Après-ski бар', 'Музыка и напитки после катания', ''),
            ],
            ('SPA и бассейн', 'spa'): [
                ('Бассейн', 'Подогреваемый бассейн с видом на горы', 'бесплатно для гостей'),
                ('Сауна и хаммам', '', 'от 2 000 сом / час'),
                ('Массаж', 'Спортивный и расслабляющий', 'от 2 500 сом'),
            ],
        }
        for i, ((name, slug), services) in enumerate(categories.items()):
            category, created = ServiceCategory.objects.get_or_create(slug=slug, defaults={'name': name, 'order': i})
            if created:
                for j, (s_name, desc, price) in enumerate(services):
                    Service.objects.create(category=category, name=s_name, description=desc, price=price, order=j)

    def menu(self):
        menu = {
            'Горячие блюда': [
                ('Лагман', 'Домашняя лапша, говядина, овощи', '350 г', 380, True),
                ('Плов', 'Рис, баранина, морковь, нут', '300 г', 360, False),
                ('Манты', 'С бараниной и тыквой, 5 шт.', '300 г', 340, False),
                ('Шорпо', 'Наваристый суп из баранины', '400 мл', 320, False),
            ],
            'Выпечка': [
                ('Самса', 'С говядиной', '1 шт.', 120, True),
                ('Боорсоки', 'С каймаком и вареньем', '150 г', 180, False),
            ],
            'Напитки': [
                ('Чай травяной', 'Чабрец, шиповник, мёд', '0,5 л', 150, False),
                ('Глинтвейн безалкогольный', 'Вишнёвый сок, специи, цитрусы', '0,3 л', 220, True),
                ('Кофе американо', '', '0,25 л', 160, False),
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
            ('Бишкек → курорт', 'Центр города, площадь Ала-Тоо', 'Сб и вс в 7:00', '~2,5 часа', 800),
            ('Курорт → Бишкек', 'Нижняя станция подъёмника', 'Сб и вс в 17:30', '~2,5 часа', 800),
            ('Индивидуальный', 'Из любой точки Бишкека', 'В любое время по заявке', '~2,5 часа', 7000),
        ]
        for i, (name, point, schedule, duration, price) in enumerate(routes):
            TransferRoute.objects.get_or_create(name=name, defaults={
                'departure_point': point, 'schedule': schedule, 'duration': duration, 'price': price,
                'price_unit': 'машину' if name == 'Индивидуальный' else 'место', 'order': i,
            })

    def offers(self):
        today = timezone.localdate()
        offers = [
            ('Раннее бронирование', 'early-booking', '−20%', 'Скидка на проживание при бронировании за 30 дней.'),
            ('Ски-пасс в подарок', 'free-skipass', 'Подарок', 'При проживании от 5 ночей — ски-пасс на 1 день бесплатно.'),
            ('Семейный уикенд', 'family-weekend', 'Семья', 'Дети до 7 лет проживают и катаются бесплатно.'),
        ]
        for i, (title, slug, label, short) in enumerate(offers):
            Offer.objects.get_or_create(slug=slug, defaults={
                'title': title, 'label': label, 'short_description': short, 'order': i,
                'content': f'<p>{short}</p><p>Условия акции уточняйте у администратора.</p>',
                'valid_to': today + timedelta(days=90),
            })

    def reviews(self):
        reviews = [
            ('Айгуль', 5, 'Отличные трассы и быстрые подъёмники, почти без очередей. '
                          'Инструктор за два дня поставил ребёнка на лыжи. Обязательно вернёмся!'),
            ('Дмитрий', 5, 'Жили в коттедже прямо у склона — вышел из двери и сразу на трассу. '
                           'Вечером сауна и ужин в ресторане. Идеальный отдых.'),
            ('Эрлан', 4, 'Брали снаряжение в прокате: всё новое, подобрали быстро. '
                         'Персонал внимательный, кафе на склоне с вкусной едой.'),
        ]
        for name, rating, text in reviews:
            Review.objects.get_or_create(name=name, text=text, defaults={'rating': rating, 'is_published': True})

    def posts(self):
        now = timezone.now()
        posts = [
            ('Открытие сезона 2026/2027', 'season-opening',
             'Рассказываем о дате открытия, новых трассах и ценах на ски-пассы в этом сезоне.', 1),
            ('Новый кресельный подъёмник', 'new-chairlift',
             'Пропускная способность выросла вдвое — меньше очередей и больше катания.', 15),
            ('Детская школа катания', 'kids-school',
             'Набираем группы для детей от 4 лет. Занятия с опытными инструкторами.', 30),
        ]
        for title, slug, excerpt, days_ago in posts:
            Post.objects.get_or_create(slug=slug, defaults={
                'title': title, 'excerpt': excerpt, 'published_at': now - timedelta(days=days_ago),
                'content': f'<p>{excerpt}</p><p>Подробности — по телефону или в разделе «Контакты».</p>',
            })

    def pages(self):
        pages = [
            ('О курорте', 'about',
             '<p>Наш курорт — это современный горнолыжный комплекс для всей семьи. '
             'Трассы для новичков и профессионалов, удобные подъёмники, '
             'проживание у самого склона и всё для отдыха после катания.</p>'),
            ('Политика конфиденциальности', 'privacy', '<p>Текст политики конфиденциальности.</p>'),
            ('Публичная оферта', 'offer', '<p>Текст публичной оферты.</p>'),
        ]
        for title, slug, content in pages:
            Page.objects.get_or_create(slug=slug, defaults={'title': title, 'content': content})

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django_resized import ResizedImageField


def image_field(upload_to, size=(1600, 1200), verbose_name='Изображение', **kwargs):
    """Картинка, которая при загрузке ужимается до size и конвертируется в WEBP."""
    return ResizedImageField(
        verbose_name, size=list(size), quality=85, force_format='WEBP',
        upload_to=upload_to, **kwargs,
    )


def tel(phone):
    """«+996 555 000 000» → «+996555000000» для ссылок tel: и wa.me."""
    return ''.join(c for c in phone if c.isdigit() or c == '+')


class RichTextField(models.TextField):
    """HTML-текст. В админке редактируется визуальным редактором Unfold."""

    def formfield(self, **kwargs):
        from unfold.contrib.forms.widgets import WysiwygWidget

        kwargs.setdefault('widget', WysiwygWidget)
        return super().formfield(**kwargs)


# =============================================================================
# АБСТРАКТНЫЕ МОДЕЛИ
# =============================================================================

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Изменено', auto_now=True)

    class Meta:
        abstract = True


class SEOModel(models.Model):
    seo_title = models.CharField('SEO title', max_length=255, blank=True)
    seo_description = models.CharField('SEO description', max_length=500, blank=True)

    class Meta:
        abstract = True


class OrderedModel(models.Model):
    order = models.PositiveIntegerField('Порядок', default=0, db_index=True)
    is_active = models.BooleanField('Показывать на сайте', default=True)

    class Meta:
        abstract = True
        ordering = ['order', 'pk']


# =============================================================================
# НАСТРОЙКИ САЙТА (одна запись)
# =============================================================================

WEEKDAYS = [
    (0, 'Понедельник'), (1, 'Вторник'), (2, 'Среда'), (3, 'Четверг'),
    (4, 'Пятница'), (5, 'Суббота'), (6, 'Воскресенье'),
]
WEEKDAYS_SHORT = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']


class SiteSettings(models.Model):
    # Основное
    name = models.CharField('Название', max_length=120, default='Тоо-Ашуу')
    full_name = models.CharField('Полное название', max_length=255, blank=True)
    tagline = models.CharField('Слоган', max_length=255, blank=True)
    season = models.CharField('Сезон', max_length=60, blank=True, help_text='Например: Сезон 2026/2027')
    logo = image_field('site/', size=(600, 200), verbose_name='Логотип', blank=True)

    # Режим работы
    open_weekdays = models.CharField(
        'Рабочие дни', max_length=20, blank=True, default='5,6',
        help_text='Дни, когда работают подъёмники',
    )
    lift_hours = models.CharField('Часы работы подъёмников', max_length=60, blank=True, default='9:30 – 16:30')
    is_season_open = models.BooleanField(
        'Сезон открыт', default=True,
        help_text='Снимите галочку в межсезонье — на сайте появится «Сезон закрыт»',
    )

    # Контакты
    phone = models.CharField('Телефон', max_length=30, blank=True)
    phone_2 = models.CharField('Телефон 2', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    working_hours = models.TextField('Режим работы (текст)', blank=True, help_text='Каждая строка — отдельный пункт')
    whatsapp = models.CharField('WhatsApp', max_length=30, blank=True, help_text='Номер в любом формате')
    instagram = models.URLField('Instagram', blank=True)
    telegram = models.URLField('Telegram', blank=True)
    facebook = models.URLField('Facebook', blank=True)

    # Как добраться
    latitude = models.DecimalField('Широта', max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField('Долгота', max_digits=9, decimal_places=6, null=True, blank=True)
    map_embed_url = models.URLField(
        'Своя карта (iframe src)', max_length=1000, blank=True,
        help_text='Если пусто — карта строится по координатам',
    )
    directions = RichTextField('Как добраться', blank=True)
    transfer_contact = models.CharField('Трансфер: контактное лицо', max_length=120, blank=True)
    transfer_phone = models.CharField('Трансфер: телефон', max_length=30, blank=True)

    # О курорте (цифры)
    altitude_base = models.PositiveIntegerField('Высота: низ, м', null=True, blank=True)
    altitude_top = models.PositiveIntegerField('Высота: верх, м', null=True, blank=True)
    distance_km = models.PositiveIntegerField('Расстояние от Бишкека, км', null=True, blank=True)
    about_image = image_field('site/', verbose_name='Фото для блока «О курорте»', blank=True)

    # Сегодня на склоне
    temperature = models.SmallIntegerField('Температура на склоне, °C', null=True, blank=True)
    snow_depth = models.PositiveSmallIntegerField('Высота снега, см', null=True, blank=True)
    snow_note = models.CharField('Состояние снега', max_length=120, blank=True, help_text='Например: свежий пухляк')
    conditions_updated_at = models.DateTimeField('Условия обновлены', auto_now=True)

    class Meta:
        verbose_name = 'Настройки сайта'
        verbose_name_plural = 'Настройки сайта'

    def __str__(self):
        return 'Настройки сайта'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def phone_href(self):
        return tel(self.phone)

    @property
    def phone_2_href(self):
        return tel(self.phone_2)

    @property
    def transfer_phone_href(self):
        return tel(self.transfer_phone)

    @property
    def whatsapp_number(self):
        return tel(self.whatsapp).lstrip('+')

    @property
    def working_hours_list(self):
        return [line.strip() for line in self.working_hours.splitlines() if line.strip()]

    @property
    def open_days(self):
        return sorted(int(d) for d in self.open_weekdays.split(',') if d.strip().isdigit())

    @property
    def open_days_label(self):
        days = self.open_days
        if days == [5, 6]:
            return 'по субботам и воскресеньям'
        if days == list(range(7)):
            return 'ежедневно'
        return ', '.join(WEEKDAYS_SHORT[d] for d in days)

    @property
    def is_open_today(self):
        return self.is_season_open and timezone.localdate().weekday() in self.open_days

    @property
    def map_src(self):
        if self.map_embed_url:
            return self.map_embed_url
        if self.latitude and self.longitude:
            return f'https://www.google.com/maps?q={self.latitude},{self.longitude}&z=12&output=embed'
        return ''


# =============================================================================
# ГЛАВНАЯ
# =============================================================================

class HeroSlide(OrderedModel):
    image = image_field('home/slides/', size=(2400, 1350), blank=True)
    eyebrow = models.CharField('Надзаголовок', max_length=120, blank=True)
    title = models.CharField('Заголовок', max_length=120)
    text = models.CharField('Подзаголовок', max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Слайд на главной'
        verbose_name_plural = 'Слайды на главной'

    def __str__(self):
        return self.title


class Advantage(OrderedModel):
    icon = models.CharField(
        'Иконка', max_length=20, blank=True,
        choices=[
            ('mountain', 'Гора'), ('snow', 'Снежинка'), ('lift', 'Подъёмник'), ('sun', 'Солнце'),
            ('ski', 'Лыжи'), ('home', 'Домик'), ('food', 'Еда'), ('car', 'Трансфер'),
        ],
    )
    title = models.CharField('Заголовок', max_length=120)
    text = models.TextField('Текст')

    class Meta(OrderedModel.Meta):
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'

    def __str__(self):
        return self.title


class FAQ(OrderedModel):
    question = models.CharField('Вопрос', max_length=255)
    answer = RichTextField('Ответ')

    class Meta(OrderedModel.Meta):
        verbose_name = 'Вопрос и ответ'
        verbose_name_plural = 'Вопросы и ответы'

    def __str__(self):
        return self.question


# =============================================================================
# ТЕКСТОВЫЕ СТРАНИЦЫ
# =============================================================================

class Page(SEOModel, TimeStampedModel):
    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField(
        'URL', unique=True,
        help_text='Страница со slug «about» выводится в разделе «О курорте»',
    )
    image = image_field('pages/', blank=True)
    content = RichTextField('Содержимое', blank=True)
    is_published = models.BooleanField('Опубликована', default=True)

    class Meta:
        verbose_name = 'Страница'
        verbose_name_plural = 'Страницы'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.slug == 'about':
            return reverse('base:about')
        return reverse('base:page', args=[self.slug])

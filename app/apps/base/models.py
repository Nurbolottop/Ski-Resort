from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from django.urls import reverse
from django_resized import ResizedImageField


def image_field(upload_to, size=(1600, 1200), **kwargs):
    """Картинка, которая при загрузке ужимается до size и конвертируется в WEBP."""
    return ResizedImageField(
        'Изображение', size=list(size), quality=85, force_format='WEBP',
        upload_to=upload_to, **kwargs,
    )


def tel(phone):
    """«+996 555 000 000» → «+996555000000» для ссылок tel:."""
    return ''.join(c for c in phone if c.isdigit() or c == '+')


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

class SiteSettings(models.Model):
    name = models.CharField('Название курорта', max_length=120, default='Ski Resort')
    tagline = models.CharField('Слоган', max_length=255, blank=True)
    season = models.CharField('Сезон', max_length=60, blank=True, help_text='Например: Сезон 2026/2027')

    phone = models.CharField('Телефон', max_length=30, blank=True)
    phone_2 = models.CharField('Телефон 2', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    address = models.CharField('Адрес', max_length=255, blank=True)
    working_hours = models.TextField('Режим работы', blank=True, help_text='Каждая строка — отдельный пункт')
    map_embed_url = models.URLField(
        'Ссылка для карты (iframe src)', max_length=1000, blank=True,
        help_text='Google Maps или 2ГИС: «Поделиться» → «Встроить карту» → значение src',
    )

    whatsapp = models.CharField('WhatsApp', max_length=20, blank=True, help_text='Только цифры: 996555000000')
    instagram = models.URLField('Instagram', blank=True)
    telegram = models.URLField('Telegram', blank=True)
    facebook = models.URLField('Facebook', blank=True)

    directions = RichTextUploadingField('Как добраться', blank=True)
    transfer_contact = models.CharField('Трансфер: контактное лицо', max_length=120, blank=True)
    transfer_phone = models.CharField('Трансфер: телефон', max_length=30, blank=True)

    temperature = models.SmallIntegerField('Температура на склоне, °C', null=True, blank=True)
    snow_depth = models.PositiveSmallIntegerField('Высота снега, см', null=True, blank=True)
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
    def working_hours_list(self):
        return [line.strip() for line in self.working_hours.splitlines() if line.strip()]


# =============================================================================
# ГЛАВНАЯ
# =============================================================================

class HeroSlide(OrderedModel):
    image = image_field('home/slides/', size=(1920, 1080), blank=True)
    eyebrow = models.CharField('Надзаголовок', max_length=120, blank=True)
    title = models.CharField('Заголовок', max_length=120)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Слайд на главной'
        verbose_name_plural = 'Слайды на главной'

    def __str__(self):
        return self.title


class Advantage(OrderedModel):
    title = models.CharField('Заголовок', max_length=120)
    text = models.TextField('Текст')

    class Meta(OrderedModel.Meta):
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'

    def __str__(self):
        return self.title


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
    content = RichTextUploadingField('Содержимое', blank=True)
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

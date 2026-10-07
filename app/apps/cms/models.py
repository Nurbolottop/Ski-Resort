from ckeditor_uploader.fields import RichTextUploadingField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.base.models import OrderedModel, SEOModel, TimeStampedModel, image_field


def split_lines(text):
    return [line.strip() for line in text.splitlines() if line.strip()]


# =============================================================================
# КАТАНИЕ
# =============================================================================

class Slope(OrderedModel):
    class Level(models.TextChoices):
        GREEN = 'green', 'Зелёная'
        BLUE = 'blue', 'Синяя'
        RED = 'red', 'Красная'
        BLACK = 'black', 'Чёрная'

    name = models.CharField('Название', max_length=120)
    level = models.CharField('Сложность', max_length=10, choices=Level.choices)
    length_m = models.PositiveIntegerField('Длина, м', null=True, blank=True)
    vertical_drop_m = models.PositiveIntegerField('Перепад высот, м', null=True, blank=True)
    description = models.TextField('Описание', blank=True)
    is_open = models.BooleanField('Открыта', default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Трасса'
        verbose_name_plural = 'Трассы'

    def __str__(self):
        return self.name


class Lift(OrderedModel):
    class Type(models.TextChoices):
        GONDOLA = 'gondola', 'Гондольный'
        CHAIR = 'chair', 'Кресельный'
        DRAG = 'drag', 'Бугельный'
        CARPET = 'carpet', 'Траволатор'

    name = models.CharField('Название', max_length=120)
    lift_type = models.CharField('Тип', max_length=10, choices=Type.choices)
    length_m = models.PositiveIntegerField('Длина, м', null=True, blank=True)
    capacity = models.PositiveIntegerField('Пропускная способность, чел/ч', null=True, blank=True)
    hours = models.CharField('Часы работы', max_length=60, blank=True)
    is_open = models.BooleanField('Работает', default=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Подъёмник'
        verbose_name_plural = 'Подъёмники'

    def __str__(self):
        return self.name


class SkiPass(OrderedModel):
    name = models.CharField('Название', max_length=120)
    price = models.PositiveIntegerField('Цена, сом')
    price_child = models.PositiveIntegerField('Цена для детей, сом', null=True, blank=True)
    features = models.TextField('Что входит', blank=True, help_text='Каждая строка — отдельный пункт')
    is_featured = models.BooleanField('Выделить', default=False)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Ски-пасс'
        verbose_name_plural = 'Ски-пассы'

    def __str__(self):
        return self.name

    @property
    def features_list(self):
        return split_lines(self.features)


# =============================================================================
# ПРОЖИВАНИЕ
# =============================================================================

class Room(OrderedModel, SEOModel):
    name = models.CharField('Название', max_length=120)
    slug = models.SlugField('URL', unique=True)
    cover = image_field('rooms/covers/', blank=True)
    short_description = models.TextField('Краткое описание', blank=True)
    description = RichTextUploadingField('Описание', blank=True)
    max_guests = models.PositiveSmallIntegerField('Гостей, до', default=2)
    beds = models.CharField('Кровати', max_length=120, blank=True)
    area = models.PositiveSmallIntegerField('Площадь, м²', null=True, blank=True)
    price_from = models.PositiveIntegerField('Цена от, сом / ночь')
    amenities = models.TextField('Удобства', blank=True, help_text='Каждая строка — отдельный пункт')

    class Meta(OrderedModel.Meta):
        verbose_name = 'Номер'
        verbose_name_plural = 'Номера и жильё'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cms:room_detail', args=[self.slug])

    @property
    def amenities_list(self):
        return split_lines(self.amenities)


class RoomImage(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='images', verbose_name='Номер')
    image = image_field('rooms/gallery/')
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'Фото номера'
        verbose_name_plural = 'Фото номера'

    def __str__(self):
        return f'{self.room} — фото {self.pk}'


# =============================================================================
# УСЛУГИ
# =============================================================================

class ServiceCategory(OrderedModel, SEOModel):
    name = models.CharField('Название', max_length=120)
    slug = models.SlugField('URL', unique=True)
    cover = image_field('services/covers/', blank=True)
    description = RichTextUploadingField('Описание', blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Категория услуг'
        verbose_name_plural = 'Категории услуг'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('cms:service_category', args=[self.slug])


class Service(OrderedModel):
    category = models.ForeignKey(
        ServiceCategory, on_delete=models.CASCADE, related_name='services', verbose_name='Категория',
    )
    name = models.CharField('Название', max_length=120)
    image = image_field('services/', blank=True)
    description = models.TextField('Описание', blank=True)
    price = models.CharField('Цена', max_length=120, blank=True, help_text='Например: от 1 500 сом / час')

    class Meta(OrderedModel.Meta):
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'

    def __str__(self):
        return self.name


# =============================================================================
# МЕНЮ
# =============================================================================

class MenuCategory(OrderedModel):
    name = models.CharField('Название', max_length=120)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Раздел меню'
        verbose_name_plural = 'Меню: разделы'

    def __str__(self):
        return self.name


class MenuItem(OrderedModel):
    category = models.ForeignKey(
        MenuCategory, on_delete=models.CASCADE, related_name='items', verbose_name='Раздел',
    )
    name = models.CharField('Название', max_length=120)
    description = models.CharField('Состав / описание', max_length=255, blank=True)
    weight = models.CharField('Выход', max_length=40, blank=True, help_text='Например: 250 г, 0,5 л')
    price = models.PositiveIntegerField('Цена, сом')
    image = image_field('menu/', size=(800, 600), blank=True)
    is_hit = models.BooleanField('Хит', default=False)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Блюдо'
        verbose_name_plural = 'Меню: блюда'

    def __str__(self):
        return self.name


# =============================================================================
# ТРАНСФЕР
# =============================================================================

class TransferRoute(OrderedModel):
    name = models.CharField('Маршрут', max_length=120, help_text='Например: Бишкек → курорт')
    departure_point = models.CharField('Место отправления', max_length=255, blank=True)
    schedule = models.CharField('Расписание', max_length=255, blank=True, help_text='Например: сб и вс в 7:00')
    duration = models.CharField('В пути', max_length=60, blank=True, help_text='Например: ~2,5 часа')
    price = models.PositiveIntegerField('Цена, сом', null=True, blank=True)
    price_unit = models.CharField('Цена за', max_length=60, blank=True, default='место')
    description = models.TextField('Описание', blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Маршрут трансфера'
        verbose_name_plural = 'Трансфер'

    def __str__(self):
        return self.name


# =============================================================================
# СПЕЦПРЕДЛОЖЕНИЯ
# =============================================================================

class OfferQuerySet(models.QuerySet):
    def current(self):
        today = timezone.localdate()
        return self.filter(is_active=True).filter(
            models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=today),
        )


class Offer(OrderedModel, SEOModel, TimeStampedModel):
    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField('URL', unique=True)
    image = image_field('offers/', blank=True)
    label = models.CharField('Плашка', max_length=60, blank=True, help_text='Например: −20%')
    short_description = models.TextField('Краткое описание', blank=True)
    content = RichTextUploadingField('Описание', blank=True)
    valid_from = models.DateField('Действует с', null=True, blank=True)
    valid_to = models.DateField('Действует до', null=True, blank=True)

    objects = OfferQuerySet.as_manager()

    class Meta(OrderedModel.Meta):
        verbose_name = 'Спецпредложение'
        verbose_name_plural = 'Спецпредложения'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cms:offer_detail', args=[self.slug])


# =============================================================================
# ГАЛЕРЕЯ
# =============================================================================

class GalleryImage(OrderedModel):
    image = image_field('gallery/', size=(1920, 1440))
    caption = models.CharField('Подпись', max_length=255, blank=True)

    class Meta(OrderedModel.Meta):
        verbose_name = 'Фото галереи'
        verbose_name_plural = 'Галерея'

    def __str__(self):
        return self.caption or f'Фото {self.pk}'


# =============================================================================
# ОТЗЫВЫ
# =============================================================================

class Review(TimeStampedModel):
    name = models.CharField('Имя', max_length=120)
    rating = models.PositiveSmallIntegerField(
        'Оценка', default=5, validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField('Отзыв')
    is_published = models.BooleanField('Опубликован', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'

    def __str__(self):
        return f'{self.name} ({self.rating}★)'

    @property
    def stars(self):
        return '★' * self.rating + '☆' * (5 - self.rating)


# =============================================================================
# БЛОГ
# =============================================================================

class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(is_published=True, published_at__lte=timezone.now())


class Post(SEOModel, TimeStampedModel):
    title = models.CharField('Заголовок', max_length=255)
    slug = models.SlugField('URL', unique=True, max_length=255)
    cover = image_field('blog/', blank=True)
    excerpt = models.TextField('Анонс', blank=True)
    content = RichTextUploadingField('Текст', blank=True)
    published_at = models.DateTimeField('Дата публикации', default=timezone.now)
    is_published = models.BooleanField('Опубликована', default=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'Статья'
        verbose_name_plural = 'Блог'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('cms:post_detail', args=[self.slug])

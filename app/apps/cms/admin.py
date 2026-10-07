from django.contrib import admin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RelatedDropdownFilter
from unfold.decorators import action, display

from apps.base.admin_base import SEO_TAB, BaseAdmin, BaseStackedInline, BaseTabularInline, header
from apps.base.templatetags.site_tags import money
from apps.cms.models import (
    GalleryAlbum, GalleryImage, Lift, MenuCategory, MenuItem, Offer, Post, RentalItem, Review, Room, RoomImage,
    Service, ServiceCategory, SkiPass, Slope, TransferRoute,
)

LEVEL_LABELS = {
    'green': 'success', 'blue': 'info', 'red': 'danger', 'black': 'primary', 'freeride': 'warning',
}


# =============================================================================
# СКЛОН
# =============================================================================

@admin.register(Slope)
class SlopeAdmin(BaseAdmin):
    list_display = ('name', 'level_label', 'length_m', 'vertical_drop_m', 'is_open', 'order', 'is_active')
    list_editable = ('is_open', 'order', 'is_active')
    list_filter = (('level', ChoicesDropdownFilter), 'is_open')
    actions = ['open_all', 'close_all']
    fields = (
        'name', 'level', ('length_m', 'vertical_drop_m', 'steepness'), 'description',
        ('is_open', 'is_active'), 'order',
    )

    @display(description='Сложность', label=LEVEL_LABELS)
    def level_label(self, obj):
        return obj.level, obj.get_level_display()

    @action(description='Открыть выбранные трассы')
    def open_all(self, request, queryset):
        queryset.update(is_open=True)

    @action(description='Закрыть выбранные трассы')
    def close_all(self, request, queryset):
        queryset.update(is_open=False)


@admin.register(Lift)
class LiftAdmin(BaseAdmin):
    list_display = ('name', 'lift_type', 'length_m', 'ride_minutes', 'hours', 'is_open', 'order', 'is_active')
    list_editable = ('is_open', 'order', 'is_active')
    list_filter = ('lift_type', 'is_open')
    fields = (
        'name', 'lift_type', ('length_m', 'ride_minutes', 'capacity'), 'hours',
        ('is_open', 'is_active'), 'order',
    )


@admin.register(SkiPass)
class SkiPassAdmin(BaseAdmin):
    list_display = ('name', 'price_display', 'note', 'is_featured', 'order', 'is_active')
    list_editable = ('is_featured', 'order', 'is_active')
    fields = (('name', 'is_featured'), ('price', 'price_unit'), 'note', 'features', ('order', 'is_active'))

    @display(description='Цена', ordering='price')
    def price_display(self, obj):
        return f'{money(obj.price)} сом / {obj.price_unit}' if obj.price_unit else f'{money(obj.price)} сом'


@admin.register(RentalItem)
class RentalItemAdmin(BaseAdmin):
    list_display = ('item', 'category', 'price_day', 'price_hour', 'order', 'is_active')
    list_editable = ('price_day', 'price_hour', 'order', 'is_active')
    list_filter = (('category', ChoicesDropdownFilter),)
    search_fields = ('name',)
    fields = ('category', 'name', 'description', ('price_day', 'price_hour'), 'image', ('order', 'is_active'))

    @display(description='Позиция', header=True)
    def item(self, obj):
        return header(obj.name, obj.description, obj.image)


# =============================================================================
# ПРОЖИВАНИЕ
# =============================================================================

class RoomImageInline(BaseTabularInline):
    model = RoomImage
    extra = 1
    tab = True


@admin.register(Room)
class RoomAdmin(BaseAdmin):
    list_display = ('room', 'price_display', 'max_guests', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    inlines = [RoomImageInline]
    fieldsets = (
        ('Описание', {
            'classes': ('tab',),
            'fields': ('name', 'slug', 'cover', 'short_description', 'description'),
        }),
        ('Параметры и цена', {
            'classes': ('tab',),
            'fields': (('max_guests', 'area'), 'beds', ('price_from', 'price_unit'), 'amenities', ('order', 'is_active')),
        }),
        SEO_TAB,
    )

    @display(description='Номер', header=True)
    def room(self, obj):
        return header(obj.name, obj.beds, obj.cover)

    @display(description='Цена', ordering='price_from')
    def price_display(self, obj):
        return f'от {money(obj.price_from)} сом / {obj.price_unit}'


# =============================================================================
# УСЛУГИ, МЕНЮ, ТРАНСФЕР
# =============================================================================

class ServiceInline(BaseStackedInline):
    model = Service
    extra = 0
    tab = True
    fields = (('name', 'price'), 'description', 'image', ('order', 'is_active'))


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(BaseAdmin):
    list_display = ('category', 'services_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceInline]
    fieldsets = (
        ('Категория', {'classes': ('tab',), 'fields': ('name', 'slug', 'cover', 'description', ('order', 'is_active'))}),
        SEO_TAB,
    )

    @display(description='Категория', header=True)
    def category(self, obj):
        return header(obj.name, '', obj.cover)

    @display(description='Услуг')
    def services_count(self, obj):
        return obj.services.count()


@admin.register(Service)
class ServiceAdmin(BaseAdmin):
    list_display = ('name', 'category', 'price', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = (('category', RelatedDropdownFilter),)
    search_fields = ('name',)


class MenuItemInline(BaseTabularInline):
    model = MenuItem
    extra = 1
    tab = True
    fields = ('name', 'description', 'weight', 'price', 'image', 'is_hit', 'order', 'is_active')


@admin.register(MenuCategory)
class MenuCategoryAdmin(BaseAdmin):
    list_display = ('name', 'items_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    inlines = [MenuItemInline]

    @display(description='Блюд')
    def items_count(self, obj):
        return obj.items.count()


@admin.register(MenuItem)
class MenuItemAdmin(BaseAdmin):
    list_display = ('dish', 'category', 'weight', 'price', 'is_hit', 'order', 'is_active')
    list_editable = ('price', 'is_hit', 'order', 'is_active')
    list_filter = (('category', RelatedDropdownFilter), 'is_hit')
    search_fields = ('name',)

    @display(description='Блюдо', header=True)
    def dish(self, obj):
        return header(obj.name, obj.description, obj.image)


@admin.register(TransferRoute)
class TransferRouteAdmin(BaseAdmin):
    list_display = ('name', 'schedule', 'duration', 'price', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    fields = ('name', 'departure_point', ('schedule', 'duration'), ('price', 'price_unit'), 'description',
              ('order', 'is_active'))


# =============================================================================
# КОНТЕНТ
# =============================================================================

@admin.register(Offer)
class OfferAdmin(BaseAdmin):
    list_display = ('offer', 'valid_from', 'valid_to', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    search_fields = ('title',)
    fieldsets = (
        ('Акция', {
            'classes': ('tab',),
            'fields': ('title', 'slug', 'image', 'label', 'short_description', 'content'),
        }),
        ('Срок и показ', {'classes': ('tab',), 'fields': (('valid_from', 'valid_to'), ('order', 'is_active'))}),
        SEO_TAB,
    )

    @display(description='Акция', header=True)
    def offer(self, obj):
        return header(obj.title, obj.label, obj.image)


class GalleryImageInline(BaseTabularInline):
    model = GalleryImage
    extra = 3
    tab = True
    fields = ('image', 'caption', 'order', 'is_active')


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(BaseAdmin):
    list_display = ('title', 'images_count', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [GalleryImageInline]

    @display(description='Фото')
    def images_count(self, obj):
        return obj.images.count()


@admin.register(GalleryImage)
class GalleryImageAdmin(BaseAdmin):
    list_display = ('photo', 'album', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = (('album', RelatedDropdownFilter),)

    @display(description='Фото', header=True)
    def photo(self, obj):
        return header(obj.caption or f'Фото {obj.pk}', '', obj.image)


@admin.register(Review)
class ReviewAdmin(BaseAdmin):
    list_display = ('name', 'rating_display', 'short_text', 'status', 'created_at')
    list_filter = ('is_published', 'rating')
    search_fields = ('name', 'text')
    actions = ['publish', 'unpublish']

    @display(description='Оценка', ordering='rating')
    def rating_display(self, obj):
        return obj.stars

    @display(description='Отзыв')
    def short_text(self, obj):
        return obj.text[:90]

    @display(description='Статус', label={'Опубликован': 'success', 'На модерации': 'warning'})
    def status(self, obj):
        return 'Опубликован' if obj.is_published else 'На модерации'

    @action(description='Опубликовать выбранные')
    def publish(self, request, queryset):
        queryset.update(is_published=True)

    @action(description='Снять с публикации')
    def unpublish(self, request, queryset):
        queryset.update(is_published=False)


@admin.register(Post)
class PostAdmin(BaseAdmin):
    list_display = ('post', 'published_at', 'is_published')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    search_fields = ('title',)
    fieldsets = (
        ('Статья', {
            'classes': ('tab',),
            'fields': ('title', 'slug', 'cover', 'excerpt', 'content', ('published_at', 'is_published')),
        }),
        SEO_TAB,
    )

    @display(description='Статья', header=True)
    def post(self, obj):
        return header(obj.title, obj.excerpt[:60], obj.cover)

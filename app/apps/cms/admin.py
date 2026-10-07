from django.contrib import admin

from apps.cms.models import (
    GalleryImage, Lift, MenuCategory, MenuItem, Offer, Post, Review, Room, RoomImage, Service, ServiceCategory,
    SkiPass, Slope, TransferRoute,
)

SEO_FIELDSET = ('SEO', {'fields': ('seo_title', 'seo_description'), 'classes': ('collapse',)})


@admin.register(Slope)
class SlopeAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'length_m', 'is_open', 'order', 'is_active')
    list_editable = ('is_open', 'order', 'is_active')
    list_filter = ('level', 'is_open')


@admin.register(Lift)
class LiftAdmin(admin.ModelAdmin):
    list_display = ('name', 'lift_type', 'hours', 'is_open', 'order', 'is_active')
    list_editable = ('is_open', 'order', 'is_active')
    list_filter = ('lift_type', 'is_open')


@admin.register(SkiPass)
class SkiPassAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'price_child', 'is_featured', 'order', 'is_active')
    list_editable = ('price', 'price_child', 'is_featured', 'order', 'is_active')


class RoomImageInline(admin.TabularInline):
    model = RoomImage
    extra = 1


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_from', 'max_guests', 'order', 'is_active')
    list_editable = ('price_from', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [RoomImageInline]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'cover', 'short_description', 'description')}),
        ('Параметры', {'fields': ('max_guests', 'beds', 'area', 'price_from', 'amenities')}),
        ('Отображение', {'fields': ('order', 'is_active')}),
        SEO_FIELDSET,
    )


class ServiceInline(admin.StackedInline):
    model = Service
    extra = 0


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ServiceInline]
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'cover', 'description', 'order', 'is_active')}),
        SEO_FIELDSET,
    )


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('category',)


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1
    fields = ('name', 'description', 'weight', 'price', 'image', 'is_hit', 'order', 'is_active')


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    inlines = [MenuItemInline]


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'weight', 'price', 'is_hit', 'order', 'is_active')
    list_editable = ('price', 'is_hit', 'order', 'is_active')
    list_filter = ('category', 'is_hit')
    search_fields = ('name',)


@admin.register(TransferRoute)
class TransferRouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'schedule', 'duration', 'price', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'label', 'valid_from', 'valid_to', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'image', 'label', 'short_description', 'content')}),
        ('Срок действия', {'fields': ('valid_from', 'valid_to')}),
        ('Отображение', {'fields': ('order', 'is_active')}),
        SEO_FIELDSET,
    )


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating', 'short_text', 'is_published', 'created_at')
    list_editable = ('is_published',)
    list_filter = ('is_published', 'rating')
    actions = ['publish']

    @admin.display(description='Отзыв')
    def short_text(self, obj):
        return obj.text[:80]

    @admin.action(description='Опубликовать выбранные')
    def publish(self, request, queryset):
        queryset.update(is_published=True)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'published_at', 'is_published')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'published_at'
    search_fields = ('title',)
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'cover', 'excerpt', 'content', 'published_at', 'is_published')}),
        SEO_FIELDSET,
    )

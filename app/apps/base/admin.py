from django.contrib import admin

from apps.base.models import Advantage, HeroSlide, Page, SiteSettings


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Основное', {'fields': ('name', 'tagline', 'season')}),
        ('Контакты', {'fields': ('phone', 'phone_2', 'email', 'address', 'working_hours', 'map_embed_url')}),
        ('Как добраться и трансфер', {'fields': ('directions', 'transfer_contact', 'transfer_phone')}),
        ('Мессенджеры и соцсети', {'fields': ('whatsapp', 'instagram', 'telegram', 'facebook')}),
        ('Сегодня на склоне', {
            'fields': ('temperature', 'snow_depth', 'conditions_updated_at'),
            'description': 'Количество открытых трасс и подъёмников считается автоматически.',
        }),
    )
    readonly_fields = ('conditions_updated_at',)

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'eyebrow', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Advantage)
class AdvantageAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {'fields': ('title', 'slug', 'image', 'content', 'is_published')}),
        ('SEO', {'fields': ('seo_title', 'seo_description'), 'classes': ('collapse',)}),
    )

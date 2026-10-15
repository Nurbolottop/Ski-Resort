from django import forms
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as DjangoGroupAdmin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group, User
from django.shortcuts import redirect
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm
from unfold.widgets import UnfoldAdminCheckboxSelectMultipleWidget

from apps.base.admin_base import SEO_TAB, BaseAdmin, header
from apps.base.models import FAQ, WEEKDAYS, Advantage, HeroSlide, Page, SiteSettings

# =============================================================================
# ПОЛЬЗОВАТЕЛИ — в стиле Unfold
# =============================================================================

admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(DjangoUserAdmin, BaseAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm


@admin.register(Group)
class GroupAdmin(DjangoGroupAdmin, BaseAdmin):
    pass


# =============================================================================
# НАСТРОЙКИ САЙТА
# =============================================================================

class SiteSettingsForm(forms.ModelForm):
    open_weekdays = forms.MultipleChoiceField(
        label='Рабочие дни', choices=WEEKDAYS, required=False,
        widget=UnfoldAdminCheckboxSelectMultipleWidget,
        help_text='Дни, когда работают подъёмники. На сайте показывается «Сегодня открыто / закрыто».',
    )

    class Meta:
        model = SiteSettings
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial['open_weekdays'] = [str(d) for d in self.instance.open_days]

    def clean_open_weekdays(self):
        return ','.join(sorted(self.cleaned_data['open_weekdays']))


@admin.register(SiteSettings)
class SiteSettingsAdmin(BaseAdmin):
    form = SiteSettingsForm
    readonly_fields = ('conditions_updated_at',)
    fieldsets = (
        ('Сегодня на склоне', {
            'classes': ('tab',),
            'fields': (
                ('temperature', 'snow_depth'), 'snow_note',
                ('is_season_open', 'lift_hours'), 'open_weekdays', 'conditions_updated_at',
            ),
            'description': 'Количество открытых трасс и подъёмников считается автоматически по галочкам в разделах.',
        }),
        ('Основное', {
            'classes': ('tab',),
            'fields': ('name', 'full_name', 'tagline', 'season', 'logo'),
        }),
        ('Контакты', {
            'classes': ('tab',),
            'fields': (('phone', 'phone_2'), ('email', 'whatsapp'), 'address', 'working_hours'),
        }),
        ('Соцсети', {
            'classes': ('tab',),
            'fields': ('instagram', 'telegram', 'facebook'),
        }),
        ('Как добраться', {
            'classes': ('tab',),
            'fields': (
                ('latitude', 'longitude'), 'map_embed_url', 'directions',
                ('transfer_contact', 'transfer_phone'),
            ),
        }),
        ('О базе', {
            'classes': ('tab',),
            'fields': (('altitude_base', 'altitude_top'), 'distance_km', 'about_image'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Единственная запись — сразу открываем её
        obj = SiteSettings.load()
        return redirect('admin:base_sitesettings_change', obj.pk)


# =============================================================================
# КОНТЕНТ
# =============================================================================

@admin.register(HeroSlide)
class HeroSlideAdmin(BaseAdmin):
    list_display = ('slide', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    fields = ('image', 'eyebrow', 'title', 'text', 'order', 'is_active')

    @display(description='Слайд', header=True)
    def slide(self, obj):
        return header(obj.title, obj.eyebrow, obj.image)


@admin.register(Advantage)
class AdvantageAdmin(BaseAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(FAQ)
class FAQAdmin(BaseAdmin):
    list_display = ('question', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('question',)


@admin.register(Page)
class PageAdmin(BaseAdmin):
    list_display = ('title', 'slug', 'is_published', 'updated_at')
    list_editable = ('is_published',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Страница', {'classes': ('tab',), 'fields': ('title', 'slug', 'image', 'content', 'is_published')}),
        SEO_TAB,
    )

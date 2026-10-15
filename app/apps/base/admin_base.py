"""Общие настройки админ-классов на базе Unfold."""
from unfold.admin import ModelAdmin, StackedInline, TabularInline
from unfold.contrib.forms.widgets import WysiwygWidget

from apps.base.models import RichTextField

SEO_TAB = ('SEO', {'fields': ('seo_title', 'seo_description'), 'classes': ('tab',)})


class BaseAdmin(ModelAdmin):
    warn_unsaved_form = True
    list_filter_submit = True
    formfield_overrides = {RichTextField: {'widget': WysiwygWidget}}


class BaseTabularInline(TabularInline):
    formfield_overrides = {RichTextField: {'widget': WysiwygWidget}}


class BaseStackedInline(StackedInline):
    formfield_overrides = {RichTextField: {'widget': WysiwygWidget}}


def header(title, subtitle='', image=None):
    """Значение для @display(header=True): заголовок, подпись и миниатюра."""
    initials = ''.join(word[0] for word in str(title).split()[:2]).upper()
    picture = {'path': image.url, 'squared': True, 'width': 64, 'height': 44} if image else None
    return [title, subtitle, initials, picture]

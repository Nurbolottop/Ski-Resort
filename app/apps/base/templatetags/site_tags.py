import os

from django import template
from django.conf import settings
from django.templatetags.static import static
from django.utils.safestring import mark_safe
from PIL import Image, ImageOps

register = template.Library()


@register.filter
def money(value):
    """15000 → «15 000» (с неразрывным пробелом)."""
    try:
        return f'{int(value):,}'.replace(',', ' ')
    except (TypeError, ValueError):
        return value


@register.filter
def ru_plural(value, forms):
    """{{ 5|ru_plural:"трасса,трассы,трасс" }} → «трасс»."""
    one, few, many = forms.split(',')
    n = abs(int(value)) % 100
    if 11 <= n <= 19:
        return many
    n %= 10
    if n == 1:
        return one
    if 2 <= n <= 4:
        return few
    return many


@register.filter
def cycle_variant(value, count=3):
    """Номер заглушки-пейзажа по порядковому номеру: 1, 2, 3, 1, 2…"""
    try:
        return (int(value) - 1) % int(count) + 1
    except (TypeError, ValueError):
        return 1


@register.filter
def instagram_handle(url):
    """https://www.instagram.com/tooashuu.kg/ → @tooashuu.kg"""
    handle = str(url).rstrip('/').rsplit('/', 1)[-1]
    return f'@{handle}' if handle and 'instagram.com' not in handle else 'Instagram'


# -----------------------------------------------------------------------------
# Адаптивные картинки: WebP-копии нужной ширины, создаются при первом запросе
# -----------------------------------------------------------------------------
THUMB_WIDTHS = (480, 960, 1600)
PHOTO_WIDTHS = (640, 1024, 1600)


def _thumb_path(name, width):
    stem = os.path.splitext(name)[0]
    return f'_thumbs/{stem}-w{width}.webp'


def _make_thumb(image, width):
    """Путь к копии шириной width (или None, если исходник уже не шире)."""
    rel = _thumb_path(image.name, width)
    dst = os.path.join(settings.MEDIA_ROOT, rel)
    if os.path.exists(dst):
        return rel
    try:
        with Image.open(image.path) as im:
            if im.width <= width:
                return None
            im = ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((width, width * 4), Image.LANCZOS)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            tmp = dst + '.tmp'
            im.save(tmp, 'WEBP', quality=78, method=5)
            os.replace(tmp, dst)
        return rel
    except (OSError, ValueError):
        return None


@register.filter
def thumb(image, width=960):
    """{{ obj.image|thumb:960 }} → URL WebP-копии не шире 960px (или оригинала)."""
    if not image:
        return ''
    rel = _make_thumb(image, int(width))
    return settings.MEDIA_URL + rel if rel else image.url


@register.filter
def srcset(image, widths=''):
    """{{ obj.image|srcset }} → «…-w480.webp 480w, …-w960.webp 960w, … оригинал Nw»."""
    if not image:
        return ''
    sizes = [int(w) for w in widths.split(',')] if widths else THUMB_WIDTHS
    parts = []
    for w in sizes:
        rel = _make_thumb(image, w)
        if rel:
            parts.append(f'{settings.MEDIA_URL}{rel} {w}w')
    try:
        parts.append(f'{image.url} {image.width}w')
    except (OSError, ValueError):
        pass
    return ', '.join(parts)


@register.simple_tag
def photo(name, sizes='100vw', cls='', eager=False):
    """Фото из static/img/photos/w/: <img> с srcset из готовых WebP 640/1024/1600."""
    urls = [(static(f'img/photos/w/{name}-{w}.webp'), w) for w in PHOTO_WIDTHS]
    attrs = [
        f'src="{urls[-1][0]}"',
        'srcset="' + ', '.join(f'{u} {w}w' for u, w in urls) + '"',
        f'sizes="{sizes}"',
        'alt=""',
    ]
    if cls:
        attrs.insert(0, f'class="{cls}"')
    attrs.append('fetchpriority="high"' if eager else 'loading="lazy" decoding="async"')
    return mark_safe('<img ' + ' '.join(attrs) + '>')

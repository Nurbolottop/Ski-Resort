from django import template

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

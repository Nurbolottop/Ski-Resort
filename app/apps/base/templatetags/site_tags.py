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

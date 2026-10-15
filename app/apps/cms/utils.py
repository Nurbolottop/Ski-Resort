from django.db.models import Count, Q, Sum

from apps.cms.models import Lift, Slope


def slope_conditions():
    """Сколько трасс и подъёмников открыто прямо сейчас."""
    slopes = Slope.objects.filter(is_active=True).aggregate(
        total=Count('pk'), open=Count('pk', filter=Q(is_open=True)),
    )
    lifts = Lift.objects.filter(is_active=True).aggregate(
        total=Count('pk'), open=Count('pk', filter=Q(is_open=True)),
    )
    return {'slopes': slopes, 'lifts': lifts}


def slope_levels():
    """Сводка трасс по уровням сложности: количество и общая длина в км."""
    rows = (
        Slope.objects.filter(is_active=True)
        .values('level')
        .annotate(count=Count('pk'), length=Sum('length_m'))
    )
    by_level = {row['level']: row for row in rows}
    levels = []
    for value, label in Slope.Level.choices:
        row = by_level.get(value)
        if row:
            levels.append({
                'value': value,
                'label': label,
                'count': row['count'],
                'length_km': round((row['length'] or 0) / 1000, 1),
            })
    return levels


def total_slopes_km():
    total = Slope.objects.filter(is_active=True).aggregate(total=Sum('length_m'))['total'] or 0
    return round(total / 1000, 1)

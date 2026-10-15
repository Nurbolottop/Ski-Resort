from django.db import models

from apps.base.models import TimeStampedModel


class BookingRequest(TimeStampedModel):
    class Status(models.TextChoices):
        NEW = 'new', 'Новая'
        IN_PROGRESS = 'in_progress', 'В работе'
        CONFIRMED = 'confirmed', 'Подтверждена'
        CANCELLED = 'cancelled', 'Отменена'

    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=30)
    email = models.EmailField('E-mail', blank=True)
    check_in = models.DateField('Заезд')
    check_out = models.DateField('Выезд')
    adults = models.PositiveSmallIntegerField('Взрослых', default=2)
    children = models.PositiveSmallIntegerField('Детей', default=0)
    room = models.ForeignKey(
        'cms.Room', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='booking_requests', verbose_name='Номер',
    )
    need_transfer = models.BooleanField('Нужен трансфер', default=False)
    comment = models.TextField('Комментарий', blank=True)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заявка на бронирование'
        verbose_name_plural = 'Заявки на бронирование'

    def __str__(self):
        return f'{self.name}: {self.check_in:%d.%m} – {self.check_out:%d.%m.%Y}'


class ContactMessage(TimeStampedModel):
    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=30, blank=True)
    email = models.EmailField('E-mail', blank=True)
    message = models.TextField('Сообщение')
    is_processed = models.BooleanField('Обработано', default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения с сайта'

    def __str__(self):
        return f'{self.name} — {self.created_at:%d.%m.%Y %H:%M}'


class Subscriber(models.Model):
    email = models.EmailField('E-mail', unique=True)
    created_at = models.DateTimeField('Подписан', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Подписчик'
        verbose_name_plural = 'Подписчики'

    def __str__(self):
        return self.email

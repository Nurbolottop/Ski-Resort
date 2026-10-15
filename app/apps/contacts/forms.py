from django import forms
from django.utils import timezone

from apps.base.forms import StyledFormMixin
from apps.cms.models import Room
from apps.contacts.models import BookingRequest, ContactMessage, Subscriber


class BookingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = BookingRequest
        fields = (
            'check_in', 'check_out', 'adults', 'children', 'room',
            'name', 'phone', 'email', 'need_transfer', 'comment',
        )
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'check_out': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'adults': forms.NumberInput(attrs={'min': 1, 'max': 20}),
            'children': forms.NumberInput(attrs={'min': 0, 'max': 10}),
            'phone': forms.TextInput(attrs={'type': 'tel', 'placeholder': '+996 ___ ___ ___'}),
            'comment': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['room'].queryset = Room.objects.filter(is_active=True)
        self.fields['room'].empty_label = 'Любой подходящий'

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get('check_in')
        check_out = cleaned.get('check_out')
        if check_in and check_in < timezone.localdate():
            self.add_error('check_in', 'Дата заезда не может быть в прошлом.')
        if check_in and check_out and check_out <= check_in:
            self.add_error('check_out', 'Дата выезда должна быть позже даты заезда.')
        return cleaned


class ContactForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ('name', 'phone', 'email', 'message')
        widgets = {
            'phone': forms.TextInput(attrs={'type': 'tel'}),
            'message': forms.Textarea(attrs={'rows': 5}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('phone') and not cleaned.get('email'):
            raise forms.ValidationError('Укажите телефон или e-mail, чтобы мы могли ответить.')
        return cleaned


class SubscribeForm(forms.ModelForm):
    class Meta:
        model = Subscriber
        fields = ('email',)

    def validate_unique(self):
        # Повторная подписка — не ошибка, обрабатывается во view
        pass

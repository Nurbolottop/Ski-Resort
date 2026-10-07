from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.cms.models import Room
from apps.contacts.forms import BookingForm, ContactForm, SubscribeForm
from apps.contacts.models import Subscriber


def contacts(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Сообщение отправлено. Мы свяжемся с вами в ближайшее время.')
            return redirect('contacts:contacts')
    else:
        form = ContactForm()
    return render(request, 'contacts/contacts.html', {'form': form})


def booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка принята! Администратор свяжется с вами для подтверждения.')
            return redirect('contacts:booking')
    else:
        # Предзаполнение из виджета на главной и кнопки «Забронировать» у номера
        initial = {key: request.GET[key] for key in ('check_in', 'check_out', 'adults', 'children') if request.GET.get(key)}
        room = Room.objects.filter(slug=request.GET.get('room'), is_active=True).first()
        if room:
            initial['room'] = room
        form = BookingForm(initial=initial)
    return render(request, 'contacts/booking.html', {'form': form})


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    if form.is_valid():
        Subscriber.objects.get_or_create(email=form.cleaned_data['email'].lower())
        messages.success(request, 'Вы подписались на спецпредложения.')
    else:
        messages.error(request, 'Проверьте e-mail.')

    next_url = request.META.get('HTTP_REFERER', '/')
    if not url_has_allowed_host_and_scheme(next_url, {request.get_host()}, request.is_secure()):
        next_url = '/'
    return redirect(next_url)

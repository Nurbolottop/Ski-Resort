from django import forms

from apps.base.forms import StyledFormMixin
from apps.cms.models import Review


class ReviewForm(StyledFormMixin, forms.ModelForm):
    rating = forms.TypedChoiceField(
        label='Оценка', coerce=int, initial=5,
        choices=[(i, '★' * i) for i in range(5, 0, -1)],
    )

    class Meta:
        model = Review
        fields = ('name', 'rating', 'text')
        widgets = {'text': forms.Textarea(attrs={'rows': 5})}

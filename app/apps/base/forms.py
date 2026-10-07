from django import forms


class StyledFormMixin:
    """Добавляет полям формы CSS-класс field__input (кроме чекбоксов)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'field__input')

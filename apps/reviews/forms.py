from django import forms
from django.core.exceptions import ValidationError

from .models import Review


class ReviewForm(forms.ModelForm):
    """Form for creating and validating reviews."""

    class Meta:
        model = Review
        fields = ('name', 'email', 'rating', 'text')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше имя'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваш email (не будет опубликован)'
            }),
            'rating': forms.Select(attrs={
                'class': 'form-control'
            }),
            'text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Поделитесь своим опытом работы с сервисом'
            })
        }

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and add error classes to fields with errors.
        """
        super().__init__(*args, **kwargs)
        if self.is_bound:
            for field in self.errors:
                if field in self.fields:
                    css_class = self.fields[field].widget.attrs.get('class', '')
                    if 'is-invalid' not in css_class:
                        self.fields[field].widget.attrs['class'] = f"{css_class} is-invalid"

    def clean_text(self) -> str:
        """Validate the review text field."""
        text = self.cleaned_data.get('text', '')

        if len(text) < 10:
            raise ValidationError('Текст отзыва должен содержать минимум 10 символов.')

        if len(text) > 1000:
            raise ValidationError('Текст отзыва не должен превышать 1000 символов.')

        return text

    def clean_name(self) -> str:
        """Validate the name field."""
        name = self.cleaned_data.get('name', '')

        if len(name) < 2:
            raise ValidationError('Имя должно содержать минимум 2 символа.')

        return name

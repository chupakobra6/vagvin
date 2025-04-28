from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User


class BaseStyledForm:
    """Base class for styled forms"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()
    
    def _style_fields(self):
        """Apply common styling to all form fields"""
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            if 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = field.label or field_name.replace('_', ' ').capitalize()


class RegistrationForm(BaseStyledForm, forms.Form):
    """Registration form for new users"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Введите ваш email'})
    )

    def clean_email(self):
        """Validate that email is not already in use"""
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(BaseStyledForm, AuthenticationForm):
    """Login form for user authentication"""
    username = forms.CharField(
        label='Email',
        widget=forms.TextInput(attrs={'placeholder': 'Введите ваш email'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'placeholder': 'Введите ваш пароль'})
    )

    def clean(self):
        """Custom clean to handle email login"""
        email = self.cleaned_data.get('username', '')
        if email and '@' in email:
            username_candidate = email.split('@')[0]
            self.cleaned_data['username'] = username_candidate
        return super().clean()


class ForgotPasswordForm(BaseStyledForm, forms.Form):
    """Form for password reset requests"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Введите ваш email'})
    )

    def clean_email(self):
        """Clean and normalize email"""
        return self.cleaned_data.get('email', '').strip()


class AdditionalEmailForm(BaseStyledForm, forms.Form):
    """Form for adding additional emails"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'Введите дополнительный email'})
    )

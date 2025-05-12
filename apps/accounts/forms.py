from typing import Dict, Any

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User


class BaseStyledForm:
    """Base class for styled forms applying common form styling"""
    
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._style_fields()
    
    def _style_fields(self) -> None:
        """Apply consistent styling to all form fields"""
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'
            if 'placeholder' not in field.widget.attrs:
                field.widget.attrs['placeholder'] = field.label or field_name.replace('_', ' ').capitalize()


class RegistrationForm(BaseStyledForm, forms.Form):
    """User registration form with email validation"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Введите ваш email',
            'class': 'form-control',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Пожалуйста, введите ваш email',
            'invalid': 'Пожалуйста, введите корректный email'
        }
    )

    def clean_email(self) -> str:
        """Validate that email is not already in use"""
        email = self.cleaned_data.get('email', '').strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(BaseStyledForm, AuthenticationForm):
    """User login form supporting email-based authentication"""
    username = forms.CharField(
        label='Email',
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите ваш email',
            'class': 'form-control',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Пожалуйста, введите ваш email'
        }
    )
    
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Введите ваш пароль',
            'class': 'form-control',
            'autocomplete': 'current-password',
            'id': 'id_password'
        }),
        error_messages={
            'required': 'Пожалуйста, введите ваш пароль'
        }
    )

    error_messages = {
        'invalid_login': 'Пожалуйста, введите правильные email и пароль. Обратите внимание, что оба поля чувствительны к регистру.',
        'inactive': 'Этот аккаунт неактивен.'
    }

    def clean(self) -> Dict[str, Any]:
        """Handle email format for authentication"""
        email = self.cleaned_data.get('username', '')
        if email and '@' in email:
            username_candidate = email.split('@')[0]
            self.cleaned_data['username'] = username_candidate
        return super().clean()


class ForgotPasswordForm(BaseStyledForm, forms.Form):
    """Password reset request form"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Введите ваш email',
            'class': 'form-control',
            'autocomplete': 'email'
        }),
        error_messages={
            'required': 'Пожалуйста, введите ваш email',
            'invalid': 'Пожалуйста, введите корректный email'
        }
    )

    def clean_email(self) -> str:
        """Normalize email input"""
        return self.cleaned_data.get('email', '').strip()


class AdditionalEmailForm(BaseStyledForm, forms.Form):
    """Form for adding additional email addresses to user account"""
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'Введите дополнительный email',
            'class': 'form-control'
        }),
        error_messages={
            'required': 'Пожалуйста, введите email',
            'invalid': 'Пожалуйста, введите корректный email'
        }
    )

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

from .models import User


class RegistrationForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = email.strip()
        if User.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует.')
        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Email', widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите ваш пароль'}))

    def clean(self):
        email = self.cleaned_data.get('username')
        if email and '@' in email:
            username_candidate = email.split('@')[0]
            self.cleaned_data['username'] = username_candidate
        return super().clean()


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        email = email.strip()
        return email


class AdditionalEmailForm(forms.Form):
    email = forms.EmailField(label='Email', widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'Введите дополнительный email'}))

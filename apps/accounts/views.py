from django.shortcuts import render
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.views.generic import TemplateView, FormView
from django.utils import timezone
import random

from .forms import RegistrationForm, ForgotPasswordForm, AdditionalEmailForm
from .utils import generate_password, send_registration_email, send_password_reset_email

User = get_user_model()


class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Передаём реферальный код в шаблон, если он указан
        context['referral_code'] = self.request.GET.get('ref')
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        username = email.split('@')[0]

        if User.objects.filter(username=username).exists():
            messages.error(self.request, 'Пользователь с таким email уже зарегистрирован. Пожалуйста, войдите или восстановите пароль.')
            return self.form_invalid(form)

        # Генерируем пароль и создаём пользователя
        password = generate_password()

        user = User(
            username=username,
            email=email,
        )

        # Устанавливаем реферала, если код указан
        referral_code = self.request.GET.get('ref')
        if referral_code:
            try:
                referrer = User.objects.get(referral_code=referral_code)
                user.referral = referrer
                messages.success(self.request, 'Зафиксирован реферальный вход.')
            except User.DoesNotExist:
                pass

        # Сохраняем пользователя с сгенерированным паролем
        user.set_password(password)
        user.save()

        # Отправляем приветственное письмо
        if send_registration_email(user, password):
            messages.success(self.request, 'Регистрация успешна. Войдите в кабинет по данным из письма.')
            return super().form_valid(form)
        else:
            # Удаляем пользователя, если письмо не отправлено
            user.delete()
            messages.error(self.request, 'Не удалось отправить письмо с данными для входа. Проверьте email и попробуйте снова.')
            return self.form_invalid(form)

@login_required
def dashboard(request):
    user = request.user
    additional_emails = user.additional_emails.split(',') if user.additional_emails else []
    
    # Получаем данные пользователя для шаблона
    user_data = {
        'username': user.username,
        'email': user.email,
        'balance': user.balance,
        'overdraft': user.overdraft,
        'referral_code': user.referral_code,
        'referral_link': f"http://vagvin.ru{user.referral_link}",
        'additional_emails': additional_emails,
        'referrals_count': user.referrals.count() if hasattr(user, 'referrals') else 0,
    }
    
    return render(request, 'accounts/dashboard.html', {'user_data': user_data})


class ForgotPasswordView(FormView):
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = '/login/'

    def form_valid(self, form):
        email = form.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Пользователь с таким email не найден
            messages.error(self.request, 'Пользователь с таким email не найден.')
            return self.form_invalid(form)

        # Проверяем, не был ли недавно сброшен пароль
        if user.last_password_reset and (timezone.now() - user.last_password_reset) < timedelta(minutes=15):
            messages.error(self.request, 'Нельзя менять пароль чаще, чем раз в 15 минут.')
            return self.form_invalid(form)

        # Генерируем и устанавливаем новый пароль
        new_password = generate_password()
        user.set_password(new_password)
        user.last_password_reset = timezone.now()
        user.save()

        # Отправляем письмо с новым паролем
        if send_password_reset_email(user, new_password):
            messages.success(self.request, 'Новый пароль отправлен на ваш email.')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Не удалось отправить новый пароль. Попробуйте снова.')
            return self.form_invalid(form)

@login_required
def add_email(request):
    # Добавление дополнительного email пользователю
    if request.method == 'POST':
        form = AdditionalEmailForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user = request.user

            # Получаем текущие дополнительные email
            emails = user.additional_emails.split(',') if user.additional_emails else []

            # Проверяем, не добавлен ли уже этот email или не совпадает ли он с основным
            if email in emails or email == user.email:
                return JsonResponse({'success': False, 'message': 'Этот email уже добавлен.'}, status=400)

            # Проверяем лимит дополнительных email
            if len(emails) >= 5:
                return JsonResponse({'success': False, 'message': 'Вы не можете добавить более 5 дополнительных email.'}, status=400)

            # Добавляем email и сохраняем
            emails.append(email)
            user.additional_emails = ','.join(filter(None, emails))
            user.save(update_fields=['additional_emails'])

            return JsonResponse({'success': True, 'emails': emails})
        else:
            return JsonResponse({'success': False, 'message': 'Неверный формат email.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается.'}, status=405)

@login_required
def remove_email(request):
    # Удаление дополнительного email пользователя
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user

        # Получаем текущие дополнительные email
        emails = user.additional_emails.split(',') if user.additional_emails else []

        if email in emails:
            emails.remove(email)
            user.additional_emails = ','.join(filter(None, emails))
            user.save(update_fields=['additional_emails'])
            return JsonResponse({'success': True, 'emails': emails})
        else:
            return JsonResponse({'success': False, 'message': 'Email не найден.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается.'}, status=405)

@login_required
def update_balance(request):
    # Обновление баланса пользователя (вычитание стоимости)
    if request.method == 'POST':
        try:
            cost = float(request.POST.get('cost', 0))
            user = request.user

            # Обновляем баланс, не даём уйти в минус
            user.balance = max(0, float(user.balance) - cost)
            user.save(update_fields=['balance'])

            return JsonResponse({'success': True, 'new_balance': user.balance})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Неверное значение.'}, status=400)

    return JsonResponse({'success': False, 'message': 'Метод не поддерживается.'}, status=405)
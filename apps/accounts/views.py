import logging
import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views.generic import FormView

from .forms import RegistrationForm, ForgotPasswordForm, AdditionalEmailForm, LoginForm
from .models import User
from .utils import generate_password, send_registration_email, send_password_reset_email

logger = logging.getLogger(__name__)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
        
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('accounts:dashboard')
    else:
        form = LoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('pages:home')


# TODO: Проверить полноту и правильность валидации полей, добавить логирование
class RegisterView(FormView):
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['referral_code'] = self.request.GET.get('ref')
        return context

    def form_valid(self, form):
        email = form.cleaned_data['email']
        username = email.split('@')[0]

        try:
            if User.objects.filter(username=username).exists():
                messages.error(self.request,
                               'Пользователь с таким email уже зарегистрирован. Пожалуйста, войдите или восстановите пароль.')
                return self.form_invalid(form)

            user = User(username=username, email=email)
            while True:
                new_code = str(uuid.uuid4())[:8]
                if not User.objects.filter(referral_code=new_code).exists():
                    user.referral_code = new_code
                    break

            referral_code = self.request.GET.get('ref')
            if referral_code:
                referrer = User.objects.get(referral_code=referral_code)
                user.referral = referrer

            password = generate_password()
            email_sent = send_registration_email(user, password)

            if not email_sent:
                messages.error(self.request,
                               'Не удалось отправить письмо с данными для входа. Проверьте email и попробуйте снова.')
                return self.form_invalid(form)

            user.set_password(password)
            user.save()

            if referral_code:
                messages.success(self.request,
                                 'Вы успешно зарегистрировались по реферальной ссылке. Данные для входа отправлены на ваш email.')
            else:
                messages.success(self.request, 'Регистрация прошла успешно. Данные для входа отправлены на ваш email.')
            return super().form_valid(form)
        except Exception as e:
            logger.exception(f"Unexpected error during registration with email {email}: {str(e)}")
            messages.error(self.request,
                           f'Произошла непредвиденная ошибка при регистрации: {str(e)}. Пожалуйста, попробуйте позже.')
            return self.form_invalid(form)


class ForgotPasswordView(FormView):
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        email = form.cleaned_data['email']

        try:
            now = timezone.now()
            user = User.objects.get(email=email)
            last_reset = user.last_password_reset
            if last_reset and (now - last_reset).total_seconds() < settings.PASSWORD_RESET_TIMEOUT:
                minutes_ago = int((now - last_reset).total_seconds() // 60)
                wait_time = settings.PASSWORD_RESET_TIMEOUT // 60 - minutes_ago

                messages.info(self.request,
                               f'Пароль для этого аккаунта уже был сброшен недавно. Пожалуйста, подождите еще {wait_time} минут перед повторным запросом.')
                return redirect('login')

            new_password = generate_password()
            email_sent = send_password_reset_email(user, new_password)

            if not email_sent:
                messages.error(self.request,
                                'Произошла ошибка при отправке email. Пожалуйста, попробуйте позже или свяжитесь с поддержкой.')
                return self.form_invalid(form)

            user.set_password(new_password)
            user.last_password_reset = now
            user.save()

            messages.success(self.request, 'Новый пароль был сгенерирован и отправлен на ваш email.')
            return super().form_valid(form)
        except User.DoesNotExist:
            logger.exception(f"User with email {email} not found during password reset")
            messages.error(self.request, 'Пользователь с таким email не найден.')
            return self.form_invalid(form)
        except Exception as e:
            logger.exception(f"Unexpected error during password reset with email {email}")
            messages.error(self.request,
                           f'Произошла непредвиденная ошибка при восстановлении пароля. Пожалуйста, попробуйте позже.')
            return self.form_invalid(form)


# TODO: Отрефакторить код ниже:
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
                return JsonResponse(
                    {'success': False, 'message': 'Вы не можете добавить более 5 дополнительных email.'}, status=400)

            try:
                # Добавляем email и сохраняем
                emails.append(email)
                user.additional_emails = ','.join(filter(None, emails))
                user.save(update_fields=['additional_emails'])

                return JsonResponse({'success': True, 'emails': emails})
            except Exception as e:
                # Логирование ошибки
                logger = logging.getLogger('apps.accounts')
                logger.error(f"Error adding email {email} for user {user.username}: {str(e)}")
                return JsonResponse({'success': False, 'message': 'Произошла ошибка при добавлении email.'}, status=500)
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
            try:
                emails.remove(email)
                user.additional_emails = ','.join(filter(None, emails))
                user.save(update_fields=['additional_emails'])
                return JsonResponse({'success': True, 'emails': emails})
            except Exception as e:
                logger = logging.getLogger('apps.accounts')
                logger.error(f"Error removing email {email} for user {user.username}: {str(e)}")
                return JsonResponse({'success': False, 'message': 'Произошла ошибка при удалении email.'}, status=500)
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

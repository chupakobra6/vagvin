import string

from django.conf import settings
from django.core.mail import send_mail


def generate_password(length=12):
    """Generates a secure random password including letters, digits, and punctuation."""
    import secrets
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(characters) for _ in range(length))


# TODO: Отдельная функция для отправки письма, разделение логики отправки и содержания письма
# TODO: HTML-стилизация письма
def send_registration_email(user, password):
    """Send a welcome email with login credentials to the user"""
    subject = 'Добро пожаловать на сайт vagvin.ru !'
    referral_link = f"http://vagvin.ru{user.referral_link}"

    message = f"""
    Здравствуйте, {user.username}!
    Вы успешно зарегистрировались на нашем сайте.
    Ваши данные:
    --------------------
    Логин: {user.username}
    Пароль: {password}
    Email: {user.email}
    Сохраните эти данные и используйте их для входа.
    Запрошенные отчеты на сайте будут приходить на данный email.
    ---------------------
    Реферальная ссылка: {referral_link}
    Получайте до 5% от платежей всех пользователей зарегистрировшихся по Вашей ссылке.
    ---------------------
    С уважением,
    Команда vagvin.ru
    """

    from_email = settings.DEFAULT_FROM_EMAIL

    return send_mail(
        subject,
        message,
        from_email,
        [user.email, from_email],  # Sending a copy to the administrator
        fail_silently=False
    )


def send_password_reset_email(user, new_password):
    """Send password reset email with new credentials"""
    subject = 'Восстановление пароля'

    message = f"""
    Здравствуйте, {user.username}!
    Вы запросили восстановление пароля.
    Ваш новый пароль: {new_password}
    Используйте его для входа в ваш личный кабинет.
    С уважением,
    Команда https://vagvin.ru
    """

    from_email = settings.DEFAULT_FROM_EMAIL

    return send_mail(
        subject,
        message,
        from_email,
        [user.email],
        fail_silently=False
    )

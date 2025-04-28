import logging
import string

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


def generate_password(length=14):
    import secrets
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def send_email(subject, to_email, html_content, additional_recipients=None, copy_admin=True):
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        plain_text = strip_tags(html_content)
        recipients = [to_email]

        if additional_recipients:
            recipients.extend(additional_recipients)

        if copy_admin and from_email not in recipients:
            recipients.append(from_email)

        logger.info(f"Attempting to send email '{subject}' to {recipients}")
        result = send_mail(
            subject,
            plain_text,
            from_email,
            recipients,
            html_message=html_content,
            fail_silently=False
        )

        if result:
            logger.info(f"Email '{subject}' successfully sent to {recipients}")
            return True
        else:
            logger.error(f"Failed to send email '{subject}' to {recipients}")
            return False
    except Exception as e:
        logger.exception(f"Error sending email: {e}")
        return False


def get_registration_email_content(user, password):
    if not user or not password:
        logger.error("Missing user or password for registration email content")
        return None

    try:
        referral_link = f"http://vagvin.ru{user.referral_link}"
        context = {
            'username': user.username,
            'password': password,
            'email': user.email,
            'referral_link': referral_link
        }
        html_content = render_to_string('emails/registration.html', context)
        return html_content
    except Exception as e:
        logger.exception(f"Error generating registration email content: {e}")
        return None


def get_password_reset_email_content(user, new_password):
    if not user or not new_password:
        logger.error("Missing user or new password for reset email content")
        return None

    try:
        context = {
            'username': user.username,
            'password': new_password,
        }
        html_content = render_to_string('emails/password_reset.html', context)
        return html_content
    except Exception as e:
        logger.exception(f"Error generating password reset email content: {e}")
        return None


def send_registration_email(user, password):
    subject = 'Добро пожаловать на сайт vagvin.ru!'
    html_content = get_registration_email_content(user, password)
    if settings.DEBUG:
        logger.debug(f"Generated password for {user.email}: {password}")
    return send_email(subject, user.email, html_content)


def send_password_reset_email(user, new_password):
    subject = 'Восстановление пароля на сайте vagvin.ru'
    html_content = get_password_reset_email_content(user, new_password)
    if settings.DEBUG:
        logger.debug(f"Reset password for {user.email}: {new_password}")
    return send_email(subject, user.email, html_content, copy_admin=False)

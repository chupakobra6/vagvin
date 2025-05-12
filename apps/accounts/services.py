import logging
import uuid
from typing import Tuple, Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import User
from .utils import PasswordService, EmailService

logger = logging.getLogger(__name__)


class UserService:
    """Service for handling user-related operations"""
    
    @classmethod
    def authenticate_user(cls, email: str, password: str) -> Optional[User]:
        """Authenticate a user with email and password"""
        if not email or not password:
            return None
            
        username = email.split('@')[0] if '@' in email else email
        return authenticate(username=username, password=password)
    
    @classmethod
    @transaction.atomic
    def register_user(cls, email: str, referral_code: Optional[str] = None) -> Tuple[bool, str, Optional[User]]:
        """Register a new user"""
        if not email:
            return False, "Требуется указать адрес электронной почты", None
            
        email = email.strip()
        username = email.split('@')[0]
        
        if User.objects.filter(username=username).exists():
            return False, "Пользователь с таким адресом электронной почты уже существует", None
            
        try:
            user = User(username=username, email=email)
            user.referral_code = cls._generate_unique_referral_code()
            
            if referral_code:
                cls._process_referral(user, referral_code)
            
            password = PasswordService.generate_password()
            email_sent = EmailService.send_registration_email(user, password)
            
            if not email_sent:
                logger.error(f"Failed to send registration email to {email}")
                return False, "Не удалось отправить письмо с данными для входа", None
                
            user.set_password(password)
            user.save()
            logger.info(f"New user created: {username} ({email})")
            
            match (referral_code, user.referral):
                case (str(), _) if user.referral is not None:
                    success_message = "Регистрация с использованием реферальной ссылки успешно завершена. Данные для входа отправлены на вашу электронную почту."
                case _:
                    success_message = "Регистрация успешно завершена. Данные для входа отправлены на вашу электронную почту."
            
            return True, success_message, user
            
        except Exception:
            logger.exception(f"Unexpected error during registration with email {email}")
            return False, "Произошла непредвиденная ошибка при регистрации", None
    
    @classmethod
    def _generate_unique_referral_code(cls) -> str:
        """Generate a unique referral code"""
        while True:
            new_code = str(uuid.uuid4())[:8]
            if not User.objects.filter(referral_code=new_code).exists():
                return new_code
    
    @classmethod
    def _process_referral(cls, user: User, referral_code: str) -> None:
        """Process referral code for a new user"""
        try:
            referrer = User.objects.get(referral_code=referral_code)
            user.referral = referrer
            logger.info(f"User {user.email} registered with referral code {referral_code}")
        except User.DoesNotExist:
            logger.warning(f"Invalid referral code {referral_code} used during registration")
    
    @classmethod
    @transaction.atomic
    def reset_password(cls, email: str) -> Tuple[bool, str]:
        """Reset a user's password"""
        if not email:
            return False, "Требуется указать адрес электронной почты"
            
        try:
            now = timezone.now()
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"User with email {email} not found during password reset")
                return False, "Пользователь с таким адресом электронной почты не найден"
                
            last_reset = user.last_password_reset
            if last_reset and (now - last_reset).total_seconds() < settings.PASSWORD_RESET_TIMEOUT:
                minutes_ago = int((now - last_reset).total_seconds() // 60)
                wait_time = settings.PASSWORD_RESET_TIMEOUT // 60 - minutes_ago
                
                return False, f"Пароль был недавно сброшен. Подождите ещё {wait_time} минут, прежде чем запрашивать снова."
            
            new_password = PasswordService.generate_password()
            email_sent = EmailService.send_password_reset_email(user, new_password)
            
            if not email_sent:
                logger.error(f"Failed to send password reset email to {email}")
                return False, "Не удалось отправить письмо. Попробуйте позже или обратитесь в службу поддержки."
                
            user.set_password(new_password)
            user.last_password_reset = now
            user.save(update_fields=['password', 'last_password_reset'])
            
            return True, "Новый пароль был создан и отправлен на ваш адрес электронной почты"
            
        except Exception:
            logger.exception(f"Unexpected error during password reset with email {email}")
            return False, "Произошла непредвиденная ошибка при сбросе пароля"
    
    @classmethod
    def get_user_data(cls, user: User) -> Dict[str, Any]:
        """Get user data for dashboard display"""
        if not user:
            return {}
            
        additional_emails = cls.get_additional_emails(user)
        
        return {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'balance': user.balance,
            'overdraft': user.overdraft,
            'referral_code': user.referral_code,
            'referral_link': f"http://vagvin.ru{user.referral_link}",
            'additional_emails': additional_emails,
            'referrals_count': User.objects.filter(referral=user).count(),
            'created_at': user.created_at,
        }
    
    @classmethod
    def get_additional_emails(cls, user: User) -> List[str]:
        """Get list of additional emails"""
        if not user.additional_emails:
            return []
        return [email.strip() for email in user.additional_emails.split(',') if email.strip()]
    
    @classmethod
    def set_additional_emails(cls, user: User, emails: List[str]) -> None:
        """Set additional emails from list"""
        user.additional_emails = '' if not emails else ','.join(emails)
    
    @classmethod
    @transaction.atomic
    def add_additional_email(cls, user: User, email: str) -> Tuple[bool, str, List[str]]:
        """Add an additional email to a user's account"""
        if not user or not email:
            return False, "Требуются данные пользователя и email", []
            
        emails = cls.get_additional_emails(user)
        email = email.strip()
        
        match (email, emails):
            case (e, _) if e == user.email:
                return False, "Этот email уже добавлен", emails
            case (e, lst) if e in lst:
                return False, "Этот email уже добавлен", emails
            case (_, lst) if len(lst) >= 5:
                return False, "Вы не можете добавить более 5 дополнительных email-адресов", emails
            case _:
                pass
            
        try:
            emails.append(email)
            cls.set_additional_emails(user, emails)
            user.save(update_fields=['additional_emails'])
            logger.info(f"Added additional email {email} for user {user.username}")
            
            return True, "Email успешно добавлен", emails
        except Exception:
            logger.exception(f"Error adding email {email} for user {user.username}")
            return False, "Произошла ошибка при добавлении email", emails
    
    @classmethod
    @transaction.atomic
    def remove_additional_email(cls, user: User, email: str) -> Tuple[bool, str, List[str]]:
        """Remove an additional email from a user's account"""
        if not user or not email:
            return False, "Требуются данные пользователя и email", []
            
        emails = cls.get_additional_emails(user)
        email = email.strip()
        
        if email not in emails:
            return False, "Email не найден", emails
            
        try:
            emails.remove(email)
            cls.set_additional_emails(user, emails)
            user.save(update_fields=['additional_emails'])
            logger.info(f"Removed additional email {email} for user {user.username}")
            
            return True, "Email успешно удален", emails
        except Exception:
            logger.exception(f"Error removing email {email} for user {user.username}")
            return False, "Произошла ошибка при удалении email", emails 
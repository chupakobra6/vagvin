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
from .utils import generate_password, send_registration_email, send_password_reset_email

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
        """
        Register a new user
        
        Returns:
            Tuple[bool, str, Optional[User]]: (success, message, user)
        """
        if not email:
            return False, "Email is required", None
            
        email = email.strip()
        username = email.split('@')[0]
        
        if User.objects.filter(username=username).exists():
            return False, "User with this email already exists", None
            
        try:
            user = User(username=username, email=email)
            
            while True:
                new_code = str(uuid.uuid4())[:8]
                if not User.objects.filter(referral_code=new_code).exists():
                    user.referral_code = new_code
                    break
            
            if referral_code:
                try:
                    referrer = User.objects.get(referral_code=referral_code)
                    user.referral = referrer
                    logger.info(f"User {email} registered with referral code {referral_code}")
                except User.DoesNotExist:
                    logger.warning(f"Invalid referral code {referral_code} used during registration")
            
            password = generate_password()
            email_sent = send_registration_email(user, password)
            
            if not email_sent:
                logger.error(f"Failed to send registration email to {email}")
                return False, "Failed to send login details email", None
                
            user.set_password(password)
            user.save()
            logger.info(f"New user created: {username} ({email})")
            
            success_message = (
                "Registration successful with referral link. Login details sent to your email."
                if referral_code and user.referral 
                else "Registration successful. Login details sent to your email."
            )
            
            return True, success_message, user
            
        except Exception as e:
            logger.exception(f"Unexpected error during registration with email {email}")
            return False, "An unexpected error occurred during registration", None
    
    @classmethod
    @transaction.atomic
    def reset_password(cls, email: str) -> Tuple[bool, str]:
        """
        Reset a user's password
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not email:
            return False, "Email is required"
            
        try:
            now = timezone.now()
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                logger.warning(f"User with email {email} not found during password reset")
                return False, "User with this email not found"
                
            last_reset = user.last_password_reset
            if last_reset and (now - last_reset).total_seconds() < settings.PASSWORD_RESET_TIMEOUT:
                minutes_ago = int((now - last_reset).total_seconds() // 60)
                wait_time = settings.PASSWORD_RESET_TIMEOUT // 60 - minutes_ago
                
                return False, f"Password was recently reset. Please wait {wait_time} more minutes before requesting again."
            
            new_password = generate_password()
            email_sent = send_password_reset_email(user, new_password)
            
            if not email_sent:
                logger.error(f"Failed to send password reset email to {email}")
                return False, "Failed to send email. Please try again later or contact support."
                
            user.set_password(new_password)
            user.last_password_reset = now
            user.save()
            
            return True, "New password has been generated and sent to your email"
            
        except Exception as e:
            logger.exception(f"Unexpected error during password reset with email {email}")
            return False, "An unexpected error occurred during password reset"
    
    @classmethod
    def get_user_data(cls, user: User) -> Dict[str, Any]:
        """Get user data for dashboard display"""
        if not user:
            return {}
            
        additional_emails = user.additional_emails.split(',') if user.additional_emails else []
        
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
    @transaction.atomic
    def add_additional_email(cls, user: User, email: str) -> Tuple[bool, str, List[str]]:
        """
        Add an additional email to a user's account
        
        Returns:
            Tuple[bool, str, List[str]]: (success, message, emails_list)
        """
        if not user or not email:
            return False, "User and email are required", []
            
        emails = user.additional_emails.split(',') if user.additional_emails else []
        emails = [e for e in emails if e]
        
        if email in emails or email == user.email:
            return False, "This email is already added", emails
            
        if len(emails) >= 5:
            return False, "You cannot add more than 5 additional emails", emails
            
        try:
            emails.append(email)
            user.additional_emails = ','.join(emails)
            user.save(update_fields=['additional_emails'])
            logger.info(f"Added additional email {email} for user {user.username}")
            
            return True, "Email added successfully", emails
        except Exception as e:
            logger.exception(f"Error adding email {email} for user {user.username}")
            return False, "An error occurred while adding the email", emails
    
    @classmethod
    @transaction.atomic
    def remove_additional_email(cls, user: User, email: str) -> Tuple[bool, str, List[str]]:
        """
        Remove an additional email from a user's account
        
        Returns:
            Tuple[bool, str, List[str]]: (success, message, emails_list)
        """
        if not user or not email:
            return False, "User and email are required", []
            
        emails = user.additional_emails.split(',') if user.additional_emails else []
        emails = [e for e in emails if e]
        
        if email not in emails:
            return False, "Email not found", emails
            
        try:
            emails.remove(email)
            user.additional_emails = ','.join(emails)
            user.save(update_fields=['additional_emails'])
            logger.info(f"Removed additional email {email} for user {user.username}")
            
            return True, "Email removed successfully", emails
        except Exception as e:
            logger.exception(f"Error removing email {email} for user {user.username}")
            return False, "An error occurred while removing the email", emails 
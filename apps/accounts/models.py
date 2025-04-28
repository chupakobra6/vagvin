import uuid
from typing import List, Optional

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse

from vagvin.models import BaseModel


class User(AbstractUser, BaseModel):
    """Extended User model with additional fields and functionality"""
    balance = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Баланс"
    )
    overdraft = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0, 
        verbose_name="Овердрафт"
    )
    referral = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='referrals',
        verbose_name="Реферер"
    )
    referral_code = models.CharField(
        max_length=32, 
        unique=True, 
        verbose_name="Реферальный код"
    )
    last_password_reset = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name="Последний сброс пароля"
    )
    additional_emails = models.TextField(
        blank=True, 
        verbose_name="Дополнительные email (CSV)"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']

    def get_additional_emails(self) -> List[str]:
        """Get list of additional emails"""
        if not self.additional_emails:
            return []
        return [email.strip() for email in self.additional_emails.split(',') if email.strip()]
    
    def set_additional_emails(self, emails: List[str]) -> None:
        """Set additional emails from list"""
        if not emails:
            self.additional_emails = ""
        else:
            self.additional_emails = ','.join(emails)
    
    def add_additional_email(self, email: str) -> bool:
        """Add additional email if not already exists"""
        if not email:
            return False
            
        emails = self.get_additional_emails()
        email = email.strip()
        
        if email in emails or email == self.email:
            return False
            
        emails.append(email)
        self.set_additional_emails(emails)
        return True
    
    def remove_additional_email(self, email: str) -> bool:
        """Remove additional email if exists"""
        if not email:
            return False
            
        emails = self.get_additional_emails()
        email = email.strip()
        
        if email not in emails:
            return False
            
        emails.remove(email)
        self.set_additional_emails(emails)
        return True

    @property
    def referral_link(self) -> str:
        """Get referral link for invitations"""
        return reverse('accounts:register') + f"?ref={self.referral_code}"
    
    @property
    def available_balance(self) -> float:
        """Get total available balance including overdraft"""
        return float(self.balance) + float(self.overdraft)
    
    def __str__(self) -> str:
        return f"{self.username} ({self.email})"


@receiver(pre_save, sender=User)
def ensure_referral_code(sender, instance, **kwargs):
    """Ensure user always has a referral code before saving"""
    if not instance.referral_code:
        while True:
            new_code = str(uuid.uuid4())[:8]
            if not User.objects.filter(referral_code=new_code).exists():
                instance.referral_code = new_code
                break

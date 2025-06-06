import uuid
from typing import List, Any, Type

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
def ensure_referral_code(sender: Type[User], instance: User, **kwargs: Any) -> None:
    """Ensure user always has a referral code before saving"""
    if not instance.referral_code:
        while True:
            new_code = str(uuid.uuid4())[:8]
            if not User.objects.filter(referral_code=new_code).exists():
                instance.referral_code = new_code
                break

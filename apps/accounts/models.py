import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from vagvin.models import BaseModel


class User(AbstractUser, BaseModel):
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Баланс")
    overdraft = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Овердрафт")
    referral = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='referrals',
                                 verbose_name="Реферер")
    referral_code = models.CharField(max_length=32, unique=True, verbose_name="Реферальный код")
    last_password_reset = models.DateTimeField(null=True, blank=True, verbose_name="Последний сброс пароля")
    additional_emails = models.TextField(blank=True, verbose_name="Дополнительные email (CSV)")

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Fallback for ensuring referral_code always exists
        if not self.referral_code:
            while True:
                new_code = str(uuid.uuid4())[:8]
                if not User.objects.filter(referral_code=new_code).exists():
                    self.referral_code = new_code
                    break
        super().save(*args, **kwargs)

    @property
    def referral_link(self):
        return f"/register?ref={self.referral_code}"

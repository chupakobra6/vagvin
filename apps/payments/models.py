from django.conf import settings
from django.db import models


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        abstract = True


class Payment(BaseModel):
    PROVIDER_CHOICES = [
        ('robokassa', 'Robokassa'),
        ('yookassa', 'YooKassa'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Пользователь')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, verbose_name='Платежная система')
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Сумма с комиссией')
    invoice_id = models.CharField(max_length=100, unique=True, verbose_name='Идентификатор платежа')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} → {self.provider} {self.amount} руб. ({self.get_status_display()})"

    def apply_commission(self, rate=0.12):
        """Apply commission to the payment amount"""
        if not self.total_amount:
            self.total_amount = round(float(self.amount) * (1 + rate), 2)
            self.save(update_fields=['total_amount'])
        return self.total_amount

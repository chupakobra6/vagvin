import logging
from decimal import Decimal

from django.conf import settings
from django.db import models

from vagvin.models import BaseModel

logger = logging.getLogger(__name__)


class Payment(BaseModel):
    """Payment transaction record."""
    PROVIDER_CHOICES = [
        ('robokassa', 'Robokassa'),
        ('yookassa', 'YooKassa'),
        ('heleket', 'Heleket'),
        ('internal', 'Internal'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='payments'
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        verbose_name='Платежная система'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма'
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма с комиссией'
    )
    invoice_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Идентификатор платежа'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )

    class Meta:
        verbose_name = 'Платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invoice_id'], name='payment_invoice_id_idx'),
            models.Index(fields=['user', 'status'], name='payment_user_status_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.user} → {self.provider} {self.amount} руб. ({self.get_status_display()})"

    @property
    def commission_amount(self) -> Decimal:
        """Calculate the commission amount."""
        return self.total_amount - self.amount

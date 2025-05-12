from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import F

from vagvin.models import BaseModel


class Payment(BaseModel):
    """
    Model representing payment transactions in the system.
    Tracks payment details, status, and associated user.
    """
    PROVIDER_CHOICES = [
        ('robokassa', 'Robokassa'),
        ('yookassa', 'YooKassa'),
        ('heleket', 'Heleket'),
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

    def apply_commission(self, rate: float = 0.12) -> Decimal:
        """Apply commission to the payment amount"""
        if not self.total_amount:
            self.total_amount = round(float(self.amount) * (1 + rate), 2)
            self.save(update_fields=['total_amount'])
        return self.total_amount

    def mark_as_successful(self) -> None:
        """Mark payment as successful"""
        self.status = 'success'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_failed(self) -> None:
        """Mark payment as failed"""
        self.status = 'failed'
        self.save(update_fields=['status', 'updated_at'])

    def update_user_balance(self) -> bool:
        """
        Update user's balance with payment amount.
        Users in this system have a direct balance field.
        """
        try:
            self.user.balance = F('balance') + self.amount
            self.user.save(update_fields=['balance'])

            self.user.refresh_from_db()
            return True
        except Exception:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception(f'Error updating balance for user {self.user.id}')
            return False

    @property
    def is_pending(self) -> bool:
        """Check if payment is pending"""
        return self.status == 'pending'

    @property
    def is_successful(self) -> bool:
        """Check if payment is successful"""
        return self.status == 'success'

    @property
    def is_failed(self) -> bool:
        """Check if payment is failed"""
        return self.status == 'failed'

    @property
    def commission_amount(self) -> Decimal:
        """Calculate the commission amount only"""
        return self.total_amount - self.amount

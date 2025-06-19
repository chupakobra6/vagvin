import pytest
from decimal import Decimal

from apps.accounts.factories import UserFactory
from .models import Payment
from .services import PaymentService


@pytest.fixture
def user():
    """Pytest fixture for creating a user."""
    return UserFactory()


@pytest.mark.django_db
class TestPaymentModel:
    """Tests for the Payment model."""

    def test_payment_creation(self, user):
        """Test basic payment creation and properties."""
        payment = Payment.objects.create(
            user=user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending",
        )
        assert payment.user == user
        assert str(payment) == f"{user} → robokassa 100.00 руб. (Ожидает оплаты)"
        assert payment.commission_amount == Decimal("10.00")

    def test_payment_service_methods_on_model(self, user):
        """Test model-related methods from PaymentService."""
        payment = Payment.objects.create(
            user=user,
            provider="yookassa",
            amount=Decimal("200.00"),
            total_amount=Decimal("0.00"),  # To test apply_commission
            invoice_id="test_invoice_456",
            status="pending",
        )

        PaymentService.apply_commission(payment, rate=0.10)
        payment.refresh_from_db()
        assert payment.total_amount == Decimal("220.00")

        assert PaymentService.is_pending(payment)

        PaymentService.mark_as_successful(payment)
        assert PaymentService.is_successful(payment)

        # Reset status to test another state change
        payment.status = "pending"
        payment.save()

        PaymentService.mark_as_failed(payment)
        assert PaymentService.is_failed(payment)

        assert PaymentService.get_payment_method_display(payment) == "YooKassa"

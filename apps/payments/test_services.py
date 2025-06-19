import pytest
from decimal import Decimal
from unittest.mock import patch

from apps.accounts.factories import UserFactory
from .models import Payment
from .services import (
    PaymentProcessor,
    TestModePaymentProcessor,
    RobokassaPaymentProcessor,
    YookassaPaymentProcessor,
    HeleketPaymentProcessor,
    PaymentService
)


@pytest.fixture
def user():
    """Pytest fixture for creating a user with a balance."""
    return UserFactory(balance=Decimal("1000.00"))


@pytest.mark.django_db
class TestPaymentProcessor:
    """Tests for the base PaymentProcessor."""

    def test_payment_processor_base_functionality(self, user):
        """Test the core functionality of the base PaymentProcessor."""
        processor = PaymentProcessor("test_provider", 0.10)
        
        invoice_id = processor.generate_invoice_id()
        assert invoice_id.startswith("test_provider_")

        total = processor.calculate_total_amount(Decimal("100.00"))
        assert total == Decimal("110.00")

        payment = processor.create_payment(user, Decimal("100.00"))
        assert payment.provider == "test_provider"
        assert payment.amount == Decimal("100.00")
        assert payment.status == "pending"


@pytest.mark.django_db
class TestTestModePaymentProcessor:
    """Tests for the TestModePaymentProcessor."""

    def test_test_mode_payment_auto_completes(self, user):
        """Test that test payments are auto-completed and marked successful."""
        real_processor = RobokassaPaymentProcessor()
        test_processor = TestModePaymentProcessor(real_processor)
        
        initial_balance = user.balance
        payment, url = test_processor.create_payment_with_url(user, Decimal("100.00"))
        
        user.refresh_from_db()
        
        assert payment.status == "success"
        assert url.startswith("/payments/test-success/")
        # The balance update is part of the mark_payment_successful flow
        assert user.balance == initial_balance + payment.amount


@pytest.mark.django_db
class TestPaymentService:
    """Tests for the PaymentService class."""

    def test_update_balance(self, user):
        """Test updating user balance."""
        initial_balance = user.balance

        PaymentService.update_balance(user, Decimal("100.00"))
        user.refresh_from_db()
        assert user.balance == initial_balance + Decimal("100.00")

        PaymentService.update_balance(user, Decimal("-50.00"))
        user.refresh_from_db()
        assert user.balance == initial_balance + Decimal("50.00")

    def test_can_afford(self, user):
        """Test checking if user can afford a payment."""
        can_afford, _ = PaymentService.can_afford(user, Decimal("500.00"))
        assert can_afford is True

        can_afford, _ = PaymentService.can_afford(user, Decimal("1500.00"))
        assert can_afford is False

    def test_get_user_payments_stats(self, user):
        """Test getting user payment statistics."""
        Payment.objects.create(
            user=user, provider="robokassa", amount=Decimal("100.00"),
            total_amount=Decimal("110.00"), invoice_id="inv1", status="success"
        )
        Payment.objects.create(
            user=user, provider="yookassa", amount=Decimal("200.00"),
            total_amount=Decimal("220.00"), invoice_id="inv2", status="success"
        )
        Payment.objects.create(
            user=user, provider="heleket", amount=Decimal("50.00"),
            total_amount=Decimal("55.00"), invoice_id="inv3", status="pending"
        )

        stats = PaymentService.get_user_payments_stats(user)

        assert stats["successful_count"] == 2
        assert stats["pending_count"] == 1
        assert stats["successful_total"] == Decimal("300.00")

    def test_process_payment_success(self, user):
        """Test successful internal payment processing."""
        initial_balance = user.balance
        success, data = PaymentService.process_payment(user, Decimal("50.00"), "Test Purchase")
        
        user.refresh_from_db()
        assert success is True
        assert user.balance == initial_balance - Decimal("50.00")
        assert Payment.objects.filter(user=user, provider='internal', status='success').count() == 1

    def test_process_payment_insufficient_funds(self, user):
        """Test internal payment processing with insufficient funds."""
        initial_balance = user.balance
        success, data = PaymentService.process_payment(user, Decimal("2000.00"), "Expensive Purchase")
        
        user.refresh_from_db()
        assert success is False
        assert "Недостаточно средств" in data["message"]
        assert user.balance == initial_balance # Balance should not change
        assert Payment.objects.filter(user=user, provider='internal').count() == 0


@pytest.mark.django_db
class TestExternalPaymentProcessors:
    """Tests for external payment processors like YooKassa and Heleket."""

    @patch('apps.payments.services.requests.post')
    def test_yookassa_verify_callback_success(self, mock_post):
        """Test successful verification of a YooKassa callback."""
        user = UserFactory()
        payment = Payment.objects.create(
            user=user, provider='yookassa', amount=100, total_amount=110, 
            invoice_id='yookassa_123', status='pending'
        )
        callback_data = {
            "object": {
                "metadata": {"idempotence_key": "yookassa_123"},
                "status": "succeeded"
            }
        }
        processor = YookassaPaymentProcessor()
        
        with patch.object(PaymentService, 'update_user_balance', return_value=True):
            verified_payment, is_valid = processor.verify_callback(callback_data)

        payment.refresh_from_db()
        assert is_valid is True
        assert verified_payment.id == payment.id
        assert payment.status == 'success'

    @patch('apps.payments.services.requests.post')
    def test_heleket_verify_callback_paid(self, mock_post):
        """Test successful verification of a Heleket callback for 'paid' status."""
        user = UserFactory()
        payment = Payment.objects.create(
            user=user, provider='heleket', amount=100, total_amount=106, 
            invoice_id='heleket_456', status='pending'
        )
        callback_data = {"order_id": "heleket_456", "status": "paid"}
        processor = HeleketPaymentProcessor()

        with patch.object(PaymentService, 'update_user_balance', return_value=True):
            verified_payment, is_valid = processor.verify_callback(callback_data)

        payment.refresh_from_db()
        assert is_valid is True
        assert payment.status == 'success' 
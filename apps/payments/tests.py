from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse

from .models import Payment
from .services import (
    PaymentProcessor,
    RobokassaPaymentProcessor,
    TestModePaymentProcessor,
    PaymentService
)

User = get_user_model()


class PaymentModelTest(TestCase):
    """Tests for the Payment model."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )

    def test_payment_creation(self) -> None:
        """Test that a payment can be created."""
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )

        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.provider, "robokassa")
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.total_amount, Decimal("110.00"))
        self.assertEqual(payment.invoice_id, "test_invoice_123")
        self.assertEqual(payment.status, "pending")

    def test_payment_str_method(self) -> None:
        """Test the string representation of a payment."""
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )

        self.assertEqual(str(payment), f"{self.user} → robokassa 100.00 руб. (Ожидает оплаты)")

    def test_payment_methods(self) -> None:
        """Test payment model methods."""
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("0.00"),  # Will be calculated
            invoice_id="test_invoice_123",
            status="pending"
        )

        # Test apply_commission
        payment.apply_commission(rate=0.10)
        self.assertEqual(payment.total_amount, Decimal("110.00"))

        # Test status methods
        self.assertTrue(payment.is_pending)
        self.assertFalse(payment.is_successful)
        self.assertFalse(payment.is_failed)

        # Test mark_as_successful
        payment.mark_as_successful()
        self.assertEqual(payment.status, "success")
        self.assertTrue(payment.is_successful)

        # Create a new payment to test mark_as_failed
        payment2 = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_456",
            status="pending"
        )

        payment2.mark_as_failed()
        self.assertEqual(payment2.status, "failed")
        self.assertTrue(payment2.is_failed)

    def test_commission_amount(self) -> None:
        """Test commission amount calculation."""
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )

        self.assertEqual(payment.commission_amount, Decimal("10.00"))

    def test_get_payment_method_display(self) -> None:
        """Test getting payment method display name."""
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )

        self.assertEqual(payment.get_payment_method_display(), "Robokassa")


class PaymentProcessorTest(TestCase):
    """Tests for the PaymentProcessor base class."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.processor = PaymentProcessor("test_provider", 0.10)

    def test_generate_invoice_id(self) -> None:
        """Test invoice ID generation."""
        invoice_id = self.processor.generate_invoice_id()
        self.assertTrue(invoice_id.startswith("test_provider_"))
        self.assertEqual(len(invoice_id), len("test_provider_") + 32)  # provider + UUID hex

    def test_calculate_total_amount(self) -> None:
        """Test total amount calculation with commission."""
        total = self.processor.calculate_total_amount(Decimal("100.00"))
        self.assertEqual(total, Decimal("110.00"))

    def test_create_payment(self) -> None:
        """Test payment creation."""
        payment = self.processor.create_payment(self.user, Decimal("100.00"))

        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.provider, "test_provider")
        self.assertEqual(payment.amount, Decimal("100.00"))
        self.assertEqual(payment.total_amount, Decimal("110.00"))
        self.assertEqual(payment.status, "pending")


class TestModePaymentProcessorTest(TestCase):
    """Tests for the TestModePaymentProcessor."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123"
        )
        self.real_processor = RobokassaPaymentProcessor()
        self.test_processor = TestModePaymentProcessor(self.real_processor)

    def test_test_payment(self) -> None:
        """Test that test payments are auto-completed and marked successful."""
        payment, url = self.test_processor.create_payment_with_url(self.user, Decimal("100.00"))

        self.assertEqual(payment.status, "success")
        self.assertTrue(payment.is_successful)
        self.assertTrue(url.startswith("/payments/test-success/"))


class PaymentServiceTest(TestCase):
    """Tests for the PaymentService class."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            balance=Decimal("1000.00")
        )

        # Create some test payments
        Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_1",
            status="success"
        )

        Payment.objects.create(
            user=self.user,
            provider="yookassa",
            amount=Decimal("200.00"),
            total_amount=Decimal("220.00"),
            invoice_id="test_invoice_2",
            status="success"
        )

        Payment.objects.create(
            user=self.user,
            provider="heleket",
            amount=Decimal("50.00"),
            total_amount=Decimal("55.00"),
            invoice_id="test_invoice_3",
            status="pending"
        )

    def test_update_balance(self) -> None:
        """Test updating user balance."""
        initial_balance = self.user.balance

        # Test with a positive amount
        success, data = PaymentService.update_balance(self.user, Decimal("100.00"))

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, initial_balance + Decimal("100.00"))

        # Test with a negative amount
        success, data = PaymentService.update_balance(self.user, Decimal("-50.00"))

        self.assertTrue(success)
        self.user.refresh_from_db()
        self.assertEqual(self.user.balance, initial_balance + Decimal("100.00") - Decimal("50.00"))

    def test_can_afford(self) -> None:
        """Test checking if user can afford a payment."""
        # Test amount within balance
        can_afford, _ = PaymentService.can_afford(self.user, Decimal("500.00"))
        self.assertTrue(can_afford)

        # Test amount exceeding balance
        can_afford, _ = PaymentService.can_afford(self.user, Decimal("1500.00"))
        self.assertFalse(can_afford)

    def test_get_user_payments_stats(self) -> None:
        """Test getting user payment statistics."""
        stats = PaymentService.get_user_payments_stats(self.user)

        self.assertEqual(stats["payments_count"], 2)  # Only the successful payments
        self.assertEqual(stats["successful_payments"], 2)
        self.assertEqual(stats["pending_payments"], 1)
        self.assertEqual(stats["total_amount"], Decimal("300.00"))


class PaymentViewsTest(TestCase):
    """Tests for the payment views."""

    def setUp(self) -> None:
        self.client = Client()
        self.factory = RequestFactory()

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            balance=Decimal("1000.00")
        )

        self.client.login(username="testuser", password="testpass123")

    @patch('apps.payments.services.RobokassaPaymentProcessor.create_payment_with_url')
    def test_initiate_payment_view(self, mock_create_payment) -> None:
        """Test initiating a payment."""
        # Mock the payment creation
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )
        mock_create_payment.return_value = (payment, "https://test-payment-url.com")

        # Test the view
        url = reverse('payments:robokassa_initiate')
        data = {
            'amount': '100.00'
        }
        response = self.client.post(url, data=data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['payment_url'], "https://test-payment-url.com")

    def test_payment_status_view(self) -> None:
        """Test checking payment status."""
        # Create a payment for the user
        payment = Payment.objects.create(
            user=self.user,
            provider="robokassa",
            amount=Decimal("100.00"),
            total_amount=Decimal("110.00"),
            invoice_id="test_invoice_123",
            status="pending"
        )

        # Test the view
        url = reverse('payments:payment_status', args=[payment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['status'], 'pending')
        self.assertEqual(Decimal(response_data['amount']), Decimal('100.00'))

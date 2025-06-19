import pytest
from unittest.mock import patch
from django.urls import reverse
from django.test import Client, override_settings
from decimal import Decimal
import json

from apps.accounts.factories import UserFactory
from .models import Payment


@pytest.mark.django_db
class TestPaymentViews:

    @pytest.fixture
    def user(self):
        return UserFactory(balance=Decimal("100.00"))

    @pytest.fixture
    def client(self, user):
        client = Client()
        client.force_login(user)
        return client

    @patch("apps.payments.services.RobokassaPaymentProcessor.create_payment_with_url")
    def test_initiate_robokassa_payment(
        self, mock_create_payment_with_url, client, user
    ):
        """Test initiating a Robokassa payment."""
        payment = Payment(id=1, user=user, amount=Decimal("50.00"))
        mock_create_payment_with_url.return_value = (
            payment,
            "http://test-payment-url.com",
        )

        response = client.post(
            reverse("payments:robokassa_initiate"),
            data=json.dumps({"amount": "50.00"}),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["payment_url"] == "http://test-payment-url.com"
        mock_create_payment_with_url.assert_called_once()

    @override_settings(ALLOWED_ROBOKASSA_IPS=["127.0.0.1"])
    @patch("apps.payments.views.verify_robokassa_callback")
    def test_robokassa_callback_valid(self, mock_verify, client, user):
        """Test a valid Robokassa callback."""
        payment = Payment.objects.create(
            id=1,
            user=user,
            amount=100,
            total_amount=110,
            provider="robokassa",
            invoice_id="inv1",
        )
        mock_verify.return_value = (payment, True)

        # Add all required params for signature calculation
        params = {
            "Shp_invoice_id": "inv1",
            "OutSum": "110.00",
            "InvId": "123",
            "SignatureValue": "dummysignature",
        }
        response = client.get(reverse("payments:robokassa_callback"), params)

        assert response.status_code == 200
        assert response.content == b"OK1"

    @patch("apps.payments.services.verify_yookassa_callback")
    def test_yookassa_callback_invalid(self, mock_verify, client, user):
        """Test an invalid YooKassa callback."""
        payment = Payment.objects.create(
            id=2,
            user=user,
            amount=100,
            total_amount=110,
            provider="yookassa",
            invoice_id="inv2",
        )
        mock_verify.return_value = (payment, False)

        callback_data = '{"object": {"metadata": {"idempotence_key": "inv2"}}}'
        response = client.post(
            reverse("payments:yookassa_callback"),
            data=callback_data,
            content_type="application/json",
        )

        assert response.status_code == 400
        assert response.content == b"Invalid payment"

    def test_payment_status_view(self, client, user):
        """Test the payment status view for an authenticated user."""
        payment = Payment.objects.create(
            user=user,
            provider="internal",
            amount=Decimal("50.00"),
            total_amount=Decimal("50.00"),
            invoice_id="internal_123",
            status="success",
        )

        response = client.get(reverse("payments:payment_status", args=[payment.id]))
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["status"] == "success"
        assert data["amount"] == 50.0

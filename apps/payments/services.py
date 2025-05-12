import base64
import hashlib
import json
import logging
import time
import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.db import transaction
from django.db.models import F, Sum, Count

from .models import Payment

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Base class for payment processing services"""

    def __init__(self, provider_name: str, commission_rate: float):
        self.provider_name = provider_name
        self.commission_rate = commission_rate

    def generate_invoice_id(self) -> str:
        """Generate a unique invoice ID for the payment."""
        return f"{self.provider_name}_{uuid.uuid4().hex}"

    def calculate_total_amount(self, amount: Decimal) -> Decimal:
        """Calculate total amount with commission."""
        return round(float(amount) * (1 + self.commission_rate), 2)

    def create_payment(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Payment:
        """Create a payment record in the database."""
        invoice_id = self.generate_invoice_id()

        if total_amount is None:
            total_amount = self.calculate_total_amount(amount)

        return Payment.objects.create(
            user=user,
            provider=self.provider_name,
            amount=amount,
            total_amount=total_amount,
            invoice_id=invoice_id,
        )

    def mark_payment_successful(self, payment: Payment) -> bool:
        """Mark payment as successful and update user balance."""
        payment.status = 'success'
        payment.save(update_fields=['status', 'updated_at'])
        return payment.update_user_balance()

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """
        Create payment and generate payment URL.
        This method should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method")


class TestModePaymentProcessor(PaymentProcessor):
    """
    Test mode payment processor that automatically completes payments
    and redirects to a success page without actually processing payment.
    """

    def __init__(self, real_processor: PaymentProcessor):
        """
        Initialize with the real processor to mimic.
        
        Args:
            real_processor: The actual payment processor to wrap
        """
        self.real_processor = real_processor
        super().__init__(f"test_{real_processor.provider_name}", real_processor.commission_rate)

    def create_payment_url(self, payment: Payment, user) -> str:
        """
        Create a simulated payment URL that redirects to a success page immediately.
        """
        # Auto-mark the payment as successful and update user balance
        self.mark_payment_successful(payment)

        # Build a test success URL that includes payment info
        return f"/payments/test-success/?payment_id={payment.id}&amount={payment.amount}&provider={self.provider_name}"

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """
        Create a payment and auto-complete it in test mode.
        """
        payment = self.create_payment(user, amount, total_amount)
        payment_url = self.create_payment_url(payment, user)
        return payment, payment_url

    def verify_callback(self, params: Dict[str, Any]) -> Tuple[Optional[Payment], bool]:
        """
        Always verify the callback as valid in test mode.
        """
        payment_id = params.get('payment_id')
        if not payment_id:
            return None, False

        try:
            payment = Payment.objects.get(id=payment_id)
            return payment, True
        except Payment.DoesNotExist:
            return None, False

    def mark_payment_successful(self, payment: Payment) -> bool:
        """
        Mark payment as successful and update user balance.
        Overrides the parent method to ensure the balance is updated.
        """
        if payment.is_successful:
            return True

        payment.status = 'success'
        payment.save(update_fields=['status', 'updated_at'])

        # Update the user's balance with the payment amount
        success = payment.update_user_balance()

        if success:
            logger.info(f"Test payment {payment.id} marked as successful and balance updated")
        else:
            logger.exception("Failed to update balance for test payment")

        return success


class RobokassaPaymentProcessor(PaymentProcessor):
    """Robokassa payment processing service"""

    def __init__(self):
        super().__init__('robokassa', 0.1)

    @staticmethod
    def calculate_signature(*args) -> str:
        """Calculate MD5 signature for Robokassa."""
        return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()

    def create_payment_url(self, payment: Payment, user) -> str:
        """Create payment URL for Robokassa."""
        merchant_login = settings.ROBOKASSA_LOGIN
        merchant_password1 = settings.ROBOKASSA_PASSWORD1
        inv_id = int(time.time())

        receipt = {
            "sno": "usn_income",
            "items": [{
                "name": f"Пополнение баланса пользователя {user.username}",
                "quantity": 1,
                "sum": float(payment.total_amount),
                "payment_method": "full_payment",
                "payment_object": "commodity",
                "tax": "vat0"
            }]
        }
        receipt_json = json.dumps(receipt, ensure_ascii=False)

        signature = self.calculate_signature(
            merchant_login,
            payment.total_amount,
            inv_id,
            receipt_json,
            merchant_password1,
            f"Shp_invoice_id={payment.invoice_id}",
            f"Shp_user_id={user.id}"
        )

        params = {
            'MerchantLogin': merchant_login,
            'OutSum': payment.total_amount,
            'InvId': inv_id,
            'Description': f'Пополнение баланса пользователя {user.username}',
            'SignatureValue': signature,
            'Receipt': receipt_json,
            'Shp_invoice_id': payment.invoice_id,
            'Shp_user_id': user.id,
            'Culture': 'ru',
            'incCurr': 'BankCard'
        }

        return f"https://auth.robokassa.ru/Merchant/Index.aspx?{urlencode(params)}"

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """Create payment and generate payment URL."""
        payment = self.create_payment(user, amount, total_amount)
        payment_url = self.create_payment_url(payment, user)
        return payment, payment_url

    def verify_callback(self, params: Dict[str, Any]) -> Tuple[Optional[Payment], bool]:
        """Verify Robokassa callback parameters."""
        invoice_id = params.get('Shp_invoice_id')
        if not invoice_id:
            return None, False

        try:
            payment = Payment.objects.get(invoice_id=invoice_id, provider=self.provider_name, status='pending')
        except Payment.DoesNotExist:
            return None, False

        out_sum = params.get('OutSum')
        inv_id = params.get('InvId')
        signature = params.get('SignatureValue')

        merchant_password2 = settings.ROBOKASSA_PASSWORD2

        expected_signature = self.calculate_signature(
            out_sum,
            inv_id,
            merchant_password2,
            f"Shp_invoice_id={invoice_id}",
            f"Shp_user_id={payment.user.id}"
        )

        if expected_signature.lower() != signature.lower():
            return payment, False

        self.mark_payment_successful(payment)
        return payment, True


class YookassaPaymentProcessor(PaymentProcessor):
    """YooKassa payment processing service"""

    def __init__(self):
        super().__init__('yookassa', 0.1)

    def create_payment_url(self, payment: Payment, user) -> str:
        """Create payment URL for YooKassa."""
        shop_id = settings.YOOKASSA_SHOP_ID
        secret_key = settings.YOOKASSA_SECRET_KEY

        payload = {
            "amount": {
                "value": str(payment.total_amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": settings.YOOKASSA_RETURN_URL
            },
            "capture": True,
            "description": f"Пополнение баланса пользователя {user.username}",
            "metadata": {
                "user_id": str(user.id),
                "idempotence_key": payment.invoice_id
            },
            "receipt": {
                "customer": {
                    "email": user.email
                },
                "items": [
                    {
                        "description": f"Пополнение баланса. ID: {payment.invoice_id}",
                        "quantity": 1,
                        "amount": {
                            "value": str(payment.total_amount),
                            "currency": "RUB"
                        },
                        "vat_code": "2",
                        "payment_mode": "full_prepayment",
                        "payment_subject": "commodity"
                    }
                ]
            }
        }

        response = requests.post(
            "https://api.yookassa.ru/v3/payments",
            auth=(shop_id, secret_key),
            headers={
                "Idempotence-Key": payment.invoice_id,
                "Content-Type": "application/json"
            },
            json=payload
        )

        response.raise_for_status()
        response_data = response.json()

        return response_data['confirmation']['confirmation_url']

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """Create payment and generate payment URL."""
        payment = self.create_payment(user, amount, total_amount)
        payment_url = self.create_payment_url(payment, user)
        return payment, payment_url

    def verify_callback(self, data: Dict[str, Any]) -> Tuple[Optional[Payment], bool]:
        """Verify YooKassa callback data."""
        idempotence_key = data.get('object', {}).get('metadata', {}).get('idempotence_key', '')

        if not idempotence_key.startswith('yookassa_'):
            return None, False

        try:
            payment = Payment.objects.get(invoice_id=idempotence_key, provider=self.provider_name, status='pending')
        except Payment.DoesNotExist:
            return None, False

        payment_status = data.get('object', {}).get('status')

        if payment_status == 'succeeded':
            self.mark_payment_successful(payment)
            return payment, True

        return payment, False


class HelekitPaymentProcessor(PaymentProcessor):
    """Helekit payment processing service"""

    def __init__(self):
        super().__init__('heleket', 0.06)

    def create_payment_url(self, payment: Payment, user) -> str:
        """Create payment URL for Helekit."""
        merchant_id = settings.HELEKET_MERCHANT_ID
        api_key = settings.HELEKET_API_KEY

        payment_data = {
            "amount": str(payment.total_amount),
            "currency": "RUB",
            "order_id": payment.invoice_id,
            "url_return": settings.HELEKET_RETURN_URL,
            "url_success": settings.HELEKET_SUCCESS_URL,
            "url_callback": settings.HELEKET_CALLBACK_URL,
            "lifetime": 3600,
            "subtract": 4,
            "accuracy_payment_percent": 1,
            "additional_data": str(user.id)
        }

        json_data = json.dumps(payment_data)
        base64_data = base64.b64encode(json_data.encode()).decode()
        sign = hashlib.md5((base64_data + api_key).encode()).hexdigest()

        response = requests.post(
            settings.HELEKET_API_URL,
            headers={
                'merchant': merchant_id,
                'sign': sign,
                'Content-Type': 'application/json'
            },
            data=json_data
        )

        response.raise_for_status()
        result = response.json()

        return result['result']['url']

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """Create payment and generate payment URL."""
        payment = self.create_payment(user, amount, total_amount)
        payment_url = self.create_payment_url(payment, user)
        return payment, payment_url

    def verify_callback(self, params: Dict[str, Any]) -> Tuple[Optional[Payment], bool]:
        """Verify Helekit callback parameters."""
        order_id = params.get('order_id')

        if not order_id or not order_id.startswith('heleket_'):
            return None, False

        try:
            payment = Payment.objects.get(invoice_id=order_id, provider=self.provider_name, status='pending')
        except Payment.DoesNotExist:
            return None, False

        payment_status = params.get('status')

        if payment_status in ['paid', 'paid_over', 'wrong_amount']:
            self.mark_payment_successful(payment)
            return payment, True

        return payment, False


class PaymentService:
    """Service for handling payment-related operations"""

    @classmethod
    @transaction.atomic
    def update_balance(cls, user, amount: Decimal) -> Tuple[bool, Dict[str, Any]]:
        """
        Update user balance with atomic operation
        
        Args:
            user: User instance
            amount: Amount to add (positive) or subtract (negative)
            
        Returns:
            Tuple[bool, Dict]: (success, data)
        """
        if not user:
            return False, {"message": "Пользователь не найден"}

        try:
            if amount < 0:
                result = user.__class__.objects.filter(pk=user.pk).update(
                    balance=F('balance') + amount
                )
            else:
                result = user.__class__.objects.filter(pk=user.pk).update(
                    balance=F('balance') + amount
                )

            if result != 1:
                logger.exception("Failed to update balance for user")
                return False, {
                    'success': False,
                    'message': "Не удалось обновить баланс",
                    'error': True
                }

            user.refresh_from_db()

            log_action = "increased" if amount > 0 else "decreased"
            logger.info(f"Balance {log_action} for user {user.username}: {abs(amount)} = {user.balance}")

            return True, {
                "new_balance": user.balance,
                "amount": amount
            }

        except Exception:
            logger.exception("Error updating balance for user")
            return False, {
                'success': False,
                'message': "Не удалось обновить баланс",
                'error': True
            }

    @classmethod
    def can_afford(cls, user, amount: Decimal) -> Tuple[bool, str]:
        """
        Check if user can afford a payment
        
        Args:
            user: User instance
            amount: Amount to check
            
        Returns:
            Tuple[bool, str]: (can_afford, message)
        """
        if not user:
            return False, "Пользователь не найден"

        available = user.balance + user.overdraft

        if available >= amount:
            return True, ""
        else:
            needed = amount - available
            return False, f"Недостаточно средств. Вам не хватает {needed} руб. для совершения платежа."

    @classmethod
    @transaction.atomic
    def process_payment(cls, user, amount: Decimal, description: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a payment for a user
        
        Args:
            user: User instance
            amount: Amount to pay
            description: Payment description
            
        Returns:
            Tuple[bool, Dict]: (success, data)
        """
        if not user:
            return False, {"message": "Пользователь не найден"}

        can_afford, message = cls.can_afford(user, amount)
        if not can_afford:
            return False, {"message": message}

        success, data = cls.update_balance(user, -amount)
        if success:
            Payment.objects.create(
                user=user,
                provider='internal',
                amount=amount,
                total_amount=amount,
                invoice_id=f"internal_{uuid.uuid4().hex}",
                status='success'
            )
            data["description"] = description
            return True, data
        else:
            return False, data

    @classmethod
    def get_user_payments_stats(cls, user) -> Dict[str, Any]:
        """
        Get payment statistics for a user
        
        Args:
            user: User instance
            
        Returns:
            Dict: Payment statistics
        """
        all_payments = Payment.objects.filter(user=user)
        successful_payments = all_payments.filter(status='success')
        pending_payments = all_payments.filter(status='pending')

        # Calculate stats
        stats = successful_payments.aggregate(
            total_amount=Sum('amount'),
            payments_count=Count('id')
        )

        # Get last payment
        last_payment = successful_payments.order_by('-created_at').first()

        # Format decimal to 2 places to avoid precision issues
        total_amount = stats.get('total_amount') or 0
        try:
            total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except AttributeError:
            pass

        # Format user balance
        user_balance = user.balance
        try:
            user_balance = user_balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except AttributeError:
            pass

        return {
            'payments': successful_payments.order_by('-created_at')[:10],
            'payments_count': stats.get('payments_count') or 0,
            'successful_payments': successful_payments.count(),
            'pending_payments': pending_payments.count(),
            'total_amount': total_amount,
            'last_payment': last_payment,
            'balance': user_balance
        }


# Factory to get the appropriate payment processor
def get_payment_processor(provider: str) -> PaymentProcessor:
    """Factory function to get the appropriate payment processor."""
    # Use PAYMENT_TEST_MODE setting to determine whether to auto-complete payments
    use_test_mode = settings.PAYMENT_TEST_MODE

    processor = None
    match provider:
        case 'robokassa':
            processor = RobokassaPaymentProcessor()
        case 'yookassa':
            processor = YookassaPaymentProcessor()
        case 'heleket':
            processor = HelekitPaymentProcessor()
        case _:
            raise ValueError(f"Unsupported payment provider: {provider}")

    if use_test_mode:
        logger.info(f"Using TEST MODE for payment provider {provider}")
        return TestModePaymentProcessor(processor)

    return processor


# Convenience functions for backward compatibility
def create_robokassa_payment(user, amount, total_amount=None):
    processor = get_payment_processor('robokassa')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_robokassa_callback(params):
    processor = get_payment_processor('robokassa')
    return processor.verify_callback(params)


def create_yookassa_payment(user, amount, total_amount=None):
    processor = get_payment_processor('yookassa')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_yookassa_callback(data):
    processor = get_payment_processor('yookassa')
    return processor.verify_callback(data)


def create_heleket_payment(user, amount, total_amount=None):
    processor = get_payment_processor('heleket')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_heleket_callback(params):
    processor = get_payment_processor('heleket')
    return processor.verify_callback(params)

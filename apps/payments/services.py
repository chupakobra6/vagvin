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
    """Base class for payment processing services."""

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
        PaymentService.mark_as_successful(payment)
        return PaymentService.update_user_balance(payment)

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """Create payment and generate payment URL."""
        raise NotImplementedError("Subclasses must implement this method")


class TestModePaymentProcessor(PaymentProcessor):
    """Test mode payment processor that automatically completes payments."""

    def __init__(self, real_processor: PaymentProcessor):
        """Initialize with the real processor to mimic."""
        self.real_processor = real_processor
        super().__init__(f"test_{real_processor.provider_name}", real_processor.commission_rate)

    def create_payment_url(self, payment: Payment, user) -> str:
        """Create a simulated payment URL that redirects to a success page."""
        self.mark_payment_successful(payment)

        return f"/payments/test-success/?payment_id={payment.id}&amount={payment.amount}&provider={self.provider_name}"

    def create_payment_with_url(self, user, amount: Decimal, total_amount: Optional[Decimal] = None) -> Tuple[
        Payment, str]:
        """Create a payment and auto-complete it in test mode."""
        payment = self.create_payment(user, amount, total_amount)
        payment_url = self.create_payment_url(payment, user)
        return payment, payment_url

    def verify_callback(self, params: Dict[str, Any]) -> Tuple[Optional[Payment], bool]:
        """Always verify the callback as valid in test mode."""
        payment_id = params.get('payment_id')
        if not payment_id:
            return None, False

        try:
            payment = Payment.objects.get(id=payment_id)
            return payment, True
        except Payment.DoesNotExist:
            return None, False

    def mark_payment_successful(self, payment: Payment) -> bool:
        """Mark payment as successful and update user balance."""
        if PaymentService.is_successful(payment):
            return True

        PaymentService.mark_as_successful(payment)
        success = PaymentService.update_user_balance(payment)

        if success:
            logger.info(f"Test payment {payment.id} marked as successful and balance updated")
        else:
            logger.exception("Failed to update balance for test payment")

        return success


class RobokassaPaymentProcessor(PaymentProcessor):
    """Robokassa payment processing service."""

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
    """YooKassa payment processing service."""

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


class HeleketPaymentProcessor(PaymentProcessor):
    """Heleket payment processing service."""

    def __init__(self):
        super().__init__('heleket', 0.06)

    def create_payment_url(self, payment: Payment, user) -> str:
        """Create payment URL for Heleket."""
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
        """Verify Heleket callback parameters."""
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
    """Service for handling payment-related operations."""
    
    @staticmethod
    def is_pending(payment) -> bool:
        """Check if payment is pending."""
        return payment.status == 'pending'
        
    @staticmethod
    def is_successful(payment) -> bool:
        """Check if payment is successful."""
        return payment.status == 'success'
        
    @staticmethod
    def is_failed(payment) -> bool:
        """Check if payment is failed."""
        return payment.status == 'failed'
    
    @staticmethod
    def get_payment_method_display(payment) -> str:
        """Get user-friendly display of payment method."""
        return dict(Payment.PROVIDER_CHOICES).get(payment.provider, payment.provider)
    
    @staticmethod
    def apply_commission(payment, rate: float = 0.12) -> Decimal:
        """Apply commission to payment amount."""
        if not payment.total_amount:
            payment.total_amount = round(float(payment.amount) * (1 + rate), 2)
            payment.save(update_fields=['total_amount'])
        return payment.total_amount
    
    @staticmethod
    def mark_as_successful(payment) -> None:
        """Mark payment as successful."""
        payment.status = 'success'
        payment.save(update_fields=['status', 'updated_at'])
    
    @staticmethod
    def mark_as_failed(payment) -> None:
        """Mark payment as failed."""
        payment.status = 'failed'
        payment.save(update_fields=['status', 'updated_at'])
    
    @staticmethod
    def update_user_balance(payment) -> bool:
        """Update user balance with payment amount."""
        try:
            payment.user.__class__.objects.filter(pk=payment.user.pk).update(
                balance=F('balance') + payment.amount
            )
            payment.user.refresh_from_db()
            return True
        except Exception:
            logger.exception("Error updating balance for user")
            return False

    @classmethod
    @transaction.atomic
    def update_balance(cls, user, amount: Decimal) -> Tuple[bool, Dict[str, Any]]:
        """Update user balance with atomic operation."""
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
        """Check if user can afford a payment."""
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
        """Process a payment for a user."""
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
        
        return False, data
        
    @classmethod
    def get_user_payments_stats(cls, user) -> Dict[str, Any]:
        """Get payment statistics for a user."""
        if not user:
            return {}
            
        payments = Payment.objects.filter(user=user)
        
        successful = payments.filter(status='success')
        successful_count = successful.count()
        successful_total = successful.aggregate(total=Sum('amount'))['total'] or 0
        
        pending = payments.filter(status='pending')
        pending_count = pending.count()
        pending_total = pending.aggregate(total=Sum('amount'))['total'] or 0
        
        by_provider = successful.values('provider').annotate(
            count=Count('id'),
            total=Sum('amount')
        )
        
        return {
            'successful_count': successful_count,
            'successful_total': successful_total,
            'pending_count': pending_count,
            'pending_total': pending_total,
            'by_provider': {item['provider']: {
                'count': item['count'],
                'total': item['total']
            } for item in by_provider}
        }


def get_payment_processor(provider: str) -> PaymentProcessor:
    """Get the appropriate payment processor for a provider."""
    try:
        test_mode = settings.PAYMENT_TEST_MODE
    except AttributeError:
        test_mode = False
    
    match provider:
        case 'robokassa':
            processor = RobokassaPaymentProcessor()
        case 'yookassa':
            processor = YookassaPaymentProcessor()
        case 'heleket':
            processor = HeleketPaymentProcessor()
        case _:
            raise ValueError(f"Unknown payment provider: {provider}")
        
    if test_mode:
        return TestModePaymentProcessor(processor)
    
    return processor


def create_robokassa_payment(user, amount, total_amount=None):
    """Create a payment using Robokassa."""
    processor = get_payment_processor('robokassa')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_robokassa_callback(params):
    """Verify a callback from Robokassa."""
    processor = get_payment_processor('robokassa')
    return processor.verify_callback(params)


def create_yookassa_payment(user, amount, total_amount=None):
    """Create a payment using YooKassa."""
    processor = get_payment_processor('yookassa')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_yookassa_callback(data):
    """Verify a callback from YooKassa."""
    processor = get_payment_processor('yookassa')
    return processor.verify_callback(data)


def create_heleket_payment(user, amount, total_amount=None):
    """Create a payment using Heleket."""
    processor = get_payment_processor('heleket')
    return processor.create_payment_with_url(user, amount, total_amount)


def verify_heleket_callback(params):
    """Verify a callback from Heleket."""
    processor = get_payment_processor('heleket')
    return processor.verify_callback(params)

import hashlib
import json
import time
import uuid
from urllib.parse import urlencode

from django.conf import settings

from .models import Payment


def calculate_signature(*args) -> str:
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def create_robokassa_payment(user, amount):
    invoice_id = f"robokassa_{uuid.uuid4().hex}"
    payment = Payment.objects.create(
        user=user,
        provider='robokassa',
        amount=amount,
        invoice_id=invoice_id,
    )

    total_amount = payment.apply_commission(rate=0.12)

    merchant_login = settings.ROBOKASSA_LOGIN
    merchant_password1 = settings.ROBOKASSA_PASSWORD1
    inv_id = int(time.time())

    receipt = {
        "sno": "usn_income",
        "items": [{
            "name": f"Пополнение баланса пользователя {user.username}",
            "quantity": 1,
            "sum": float(total_amount),
            "payment_method": "full_payment",
            "payment_object": "commodity",
            "tax": "vat0"
        }]
    }
    receipt_json = json.dumps(receipt, ensure_ascii=False)

    signature = calculate_signature(
        merchant_login,
        total_amount,
        inv_id,
        receipt_json,
        merchant_password1,
        f"Shp_invoice_id={invoice_id}",
        f"Shp_user_id={user.id}"
    )

    params = {
        'MerchantLogin': merchant_login,
        'OutSum': total_amount,
        'InvId': inv_id,
        'Description': f'Пополнение баланса пользователя {user.username}',
        'SignatureValue': signature,
        'Receipt': receipt_json,
        'Shp_invoice_id': invoice_id,
        'Shp_user_id': user.id,
        'Culture': 'ru',
        'incCurr': 'BankCard'
    }

    payment_url = f"https://auth.robokassa.ru/Merchant/Index.aspx?{urlencode(params)}"
    return payment, payment_url


def verify_robokassa_callback(params):
    invoice_id = params.get('Shp_invoice_id')
    if not invoice_id:
        return None, False

    try:
        payment = Payment.objects.get(invoice_id=invoice_id, provider='robokassa', status='pending')
    except Payment.DoesNotExist:
        return None, False

    out_sum = params.get('OutSum')
    inv_id = params.get('InvId')
    signature = params.get('SignatureValue')

    merchant_password2 = settings.ROBOKASSA_PASSWORD2

    expected_signature = calculate_signature(
        out_sum,
        inv_id,
        merchant_password2,
        f"Shp_invoice_id={invoice_id}",
        f"Shp_user_id={payment.user.id}"
    )

    if expected_signature.lower() != signature.lower():
        return payment, False

    payment.status = 'success'
    payment.save(update_fields=['status', 'updated_at'])

    # TODO: Реализовать модель пользователя, исправить логику пополнения баланса
    try:
        if hasattr(payment.user, 'profile') and hasattr(payment.user.profile, 'balance'):
            profile = payment.user.profile
            profile.balance += float(payment.amount)
            profile.save(update_fields=['balance'])
        elif hasattr(payment.user, 'balance'):
            payment.user.balance += float(payment.amount)
            payment.user.save(update_fields=['balance'])
        else:
            import logging
            logger = logging.getLogger('django')
            logger.warning(f'Cannot update balance for user {payment.user.id}: no suitable balance field found')
    except Exception as e:
        import logging
        logger = logging.getLogger('django')
        logger.error(f'Error updating balance for user {payment.user.id}: {str(e)}')

    return payment, True

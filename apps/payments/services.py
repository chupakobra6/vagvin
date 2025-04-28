import hashlib
import json
import time
import uuid
import base64
from decimal import Decimal
from urllib.parse import urlencode

import requests
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


def create_yookassa_payment(user, amount):
    """Инициализация платежа через YooKassa"""
    invoice_id = f"yookassa_{uuid.uuid4().hex}"
    
    # Create payment record
    payment = Payment.objects.create(
        user=user,
        provider='yookassa',
        amount=amount,
        invoice_id=invoice_id,
    )
    
    # Рассчитываем сумму с комиссией 12%
    total_amount = payment.apply_commission(rate=0.12)
    
    # YooKassa API credentials
    shop_id = settings.YOOKASSA_SHOP_ID
    secret_key = settings.YOOKASSA_SECRET_KEY
    
    # Формируем тело запроса
    payload = {
        "amount": {
            "value": str(total_amount),
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
            "idempotence_key": invoice_id
        },
        "receipt": {
            "customer": {
                "email": user.email
            },
            "items": [
                {
                    "description": f"Пополнение баланса. ID: {invoice_id}",
                    "quantity": 1,
                    "amount": {
                        "value": str(total_amount),
                        "currency": "RUB"
                    },
                    "vat_code": "2",
                    "payment_mode": "full_prepayment",
                    "payment_subject": "commodity"
                }
            ]
        }
    }
    
    # Отправляем запрос в YooKassa
    response = requests.post(
        "https://api.yookassa.ru/v3/payments",
        auth=(shop_id, secret_key),
        headers={
            "Idempotence-Key": invoice_id,
            "Content-Type": "application/json"
        },
        json=payload
    )
    
    response.raise_for_status()
    response_data = response.json()
    
    # Получаем URL для перенаправления пользователя
    confirmation_url = response_data['confirmation']['confirmation_url']
    
    return payment, confirmation_url


def verify_yookassa_callback(data):
    """Обработка уведомления от YooKassa (webhook)"""
    idempotence_key = data.get('object', {}).get('metadata', {}).get('idempotence_key', '')
    
    if not idempotence_key.startswith('yookassa_'):
        return None, False
    
    try:
        payment = Payment.objects.get(invoice_id=idempotence_key, provider='yookassa', status='pending')
    except Payment.DoesNotExist:
        return None, False
    
    # Проверяем статус платежа
    payment_status = data.get('object', {}).get('status')
    
    if payment_status == 'succeeded':
        # Обновляем статус платежа
        payment.status = 'success'
        payment.save(update_fields=['status', 'updated_at'])
        
        # Пополняем баланс пользователя
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
            logger.exception(f'Error updating balance for user {payment.user.id}')
        
        return payment, True
    
    return payment, False


def create_heleket_payment(user, amount):
    """Инициализация криптоплатежа через Heleket"""
    invoice_id = f"heleket_{uuid.uuid4().hex}"
    
    # Create payment record
    payment = Payment.objects.create(
        user=user,
        provider='heleket',
        amount=amount,
        invoice_id=invoice_id,
    )
    
    # Рассчитываем сумму с комиссией 6%
    total_amount = payment.apply_commission(rate=0.06)
    
    # Heleket API credentials
    merchant_id = settings.HELEKET_MERCHANT_ID
    api_key = settings.HELEKET_API_KEY
    
    # Формируем данные запроса
    payment_data = {
        "amount": str(total_amount),
        "currency": "RUB",
        "order_id": invoice_id,
        "url_return": settings.HELEKET_RETURN_URL,
        "url_success": settings.HELEKET_SUCCESS_URL,
        "url_callback": settings.HELEKET_CALLBACK_URL,
        "lifetime": 3600,
        "subtract": 4,
        "accuracy_payment_percent": 1,
        "additional_data": str(user.id)
    }
    
    # Кодируем данные и создаем подпись
    json_data = json.dumps(payment_data)
    base64_data = base64.b64encode(json_data.encode()).decode()
    sign = hashlib.md5((base64_data + api_key).encode()).hexdigest()
    
    # Отправляем запрос в Heleket
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
    
    # Получаем URL для перенаправления пользователя
    payment_url = result['result']['url']
    
    return payment, payment_url


def verify_heleket_callback(params):
    """Обработка GET-уведомления от Heleket"""
    order_id = params.get('order_id')
    
    if not order_id or not order_id.startswith('heleket_'):
        return None, False
    
    try:
        payment = Payment.objects.get(invoice_id=order_id, provider='heleket', status='pending')
    except Payment.DoesNotExist:
        return None, False
    
    # Проверяем статус платежа
    payment_status = params.get('status')
    
    if payment_status in ['paid', 'paid_over', 'wrong_amount']:
        # Обновляем статус платежа
        payment.status = 'success'
        payment.save(update_fields=['status', 'updated_at'])
        
        # Пополняем баланс пользователя
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
            logger.exception(f'Error updating balance for user {payment.user.id}')
        
        return payment, True
    
    return payment, False

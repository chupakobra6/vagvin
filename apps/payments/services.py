import hashlib
import json
import time
import uuid
from urllib.parse import urlencode
from django.conf import settings
from .models import Payment


def calculate_signature(*args) -> str:
    """
    Создает MD5 подпись для запросов к Robokassa
    
    Args:
        *args: Параметры для подписи, объединяемые двоеточием
        
    Returns:
        str: MD5 хеш подписи
    """
    return hashlib.md5(':'.join(str(arg) for arg in args).encode()).hexdigest()


def create_robokassa_payment(user, amount):   
    """
    Создает платеж в Robokassa и возвращает URL для оплаты
    
    Args:
        user: Пользователь, который создает платеж
        amount: Сумма платежа
        
    Returns:
        tuple: (Payment, payment_url)
    """
    # Создаем запись о платеже
    invoice_id = f"robokassa_{uuid.uuid4().hex}"
    payment = Payment.objects.create(
        user=user,
        provider='robokassa',
        amount=amount,
        invoice_id=invoice_id,
    )
    
    # Применяем комиссию (12%)
    total_amount = payment.apply_commission(rate=0.12)
    
    # Получаем данные из настроек
    merchant_login = settings.ROBOKASSA_LOGIN
    merchant_password1 = settings.ROBOKASSA_PASSWORD1  # Password1 - для формирования ссылки
    inv_id = int(time.time())  # Используем timestamp как InvId

    # Формируем чек для фискализации
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
    
    # Формируем подпись
    signature = calculate_signature(
        merchant_login,
        total_amount,
        inv_id,
        receipt_json,
        merchant_password1,
        f"Shp_invoice_id={invoice_id}",
        f"Shp_user_id={user.id}"
    )
    
    # Формируем параметры для URL
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
    """
    Проверяет callback от Robokassa и обновляет статус платежа
    
    Args:
        params: словарь параметров из запроса
    
    Returns:
        tuple: (Payment, is_valid)
    """
    # Получаем идентификатор платежа
    invoice_id = params.get('Shp_invoice_id')
    if not invoice_id:
        return None, False
    
    try:
        payment = Payment.objects.get(invoice_id=invoice_id, provider='robokassa', status='pending')
    except Payment.DoesNotExist:
        return None, False
    
    # Получаем параметры для проверки подписи
    out_sum = params.get('OutSum')
    inv_id = params.get('InvId')
    signature = params.get('SignatureValue')
    
    # Пароль для проверки уведомления - второй пароль (Pass2)
    merchant_password2 = settings.ROBOKASSA_PASSWORD2
    
    # Проверяем подпись
    expected_signature = calculate_signature(
        out_sum,
        inv_id,
        merchant_password2,
        f"Shp_invoice_id={invoice_id}",
        f"Shp_user_id={payment.user.id}"
    )
    
    if expected_signature.lower() != signature.lower():
        return payment, False
    
    # Обновляем статус платежа
    payment.status = 'success'
    payment.save(update_fields=['status', 'updated_at'])
    
    # Пополняем баланс пользователя
    try:
        # Проверяем наличие профиля с балансом
        if hasattr(payment.user, 'profile') and hasattr(payment.user.profile, 'balance'):
            profile = payment.user.profile
            profile.balance += float(payment.amount)
            profile.save(update_fields=['balance'])
        # Если нет стандартного профиля, можно проверить и другие модели
        # Например, если баланс хранится в пользовательской модели User
        elif hasattr(payment.user, 'balance'):
            payment.user.balance += float(payment.amount)
            payment.user.save(update_fields=['balance'])
        else:
            # Если нет подходящей модели, логируем это
            import logging
            logger = logging.getLogger('django')
            logger.warning(f'Cannot update balance for user {payment.user.id}: no suitable balance field found')
    except Exception as e:
        import logging
        logger = logging.getLogger('django')
        logger.error(f'Error updating balance for user {payment.user.id}: {str(e)}')
    
    return payment, True

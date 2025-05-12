import json
import logging
from typing import Dict, Any

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Payment
from .services import (
    get_payment_processor,
    create_robokassa_payment, verify_robokassa_callback,
    create_yookassa_payment, verify_yookassa_callback,
    create_heleket_payment, verify_heleket_callback
)

logger = logging.getLogger(__name__)


class BasePaymentView(View):
    """Base view for initiating payments with any payment processor"""
    provider = None

    @method_decorator(login_required)
    def post(self, request):
        try:
            data = self._parse_request_data(request)
            amount = float(data.get('amount', 0))
            total_amount = float(data.get('total_amount', 0)) if data.get('total_amount') else None

            if amount <= 0:
                return JsonResponse({'error': 'Сумма должна быть положительной'}, status=400)

            payment, payment_url = self._create_payment(request.user, amount, total_amount)

            return JsonResponse({
                'success': True,
                'payment_url': payment_url,
                'payment_id': payment.id
            })
        except Exception:
            logger.exception(f'Error creating {self.provider} payment')
            return JsonResponse({
                'success': False,
                'error': 'Произошла ошибка при создании платежа'
            }, status=500)

    def _parse_request_data(self, request) -> Dict[str, Any]:
        """Parse request data from either JSON or POST"""
        return json.loads(request.body) if request.body else request.POST

    def _create_payment(self, user, amount, total_amount):
        """Should be implemented by subclasses to create a payment"""
        processor = get_payment_processor(self.provider)
        return processor.create_payment_with_url(user, amount, total_amount)


class BaseCallbackView(View):
    """Base view for payment callbacks from payment providers"""
    provider = None
    ip_whitelist_setting = None

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def check_ip_whitelist(self, request) -> bool:
        """Check if the request IP is in the whitelist, if a whitelist is configured"""
        if not self.ip_whitelist_setting:
            return True

        whitelist = getattr(settings, self.ip_whitelist_setting, None)
        if not whitelist:
            return True

        return request.META.get('REMOTE_ADDR') in whitelist

    def get(self, request):
        try:
            if not self.check_ip_whitelist(request):
                return HttpResponse("Invalid IP", status=403)

            params = request.GET.dict()
            payment, is_valid = self._verify_callback(params)

            if not payment:
                return HttpResponse("Invalid payment", status=400)

            if is_valid:
                return self._success_response(payment)
            else:
                return HttpResponse("Invalid signature or status", status=400)
        except Exception:
            logger.exception(f'Error processing {self.provider} callback')
            return HttpResponse("Error", status=500)

    def post(self, request):
        """Default implementation for POST, can be overridden by subclasses"""
        return self.get(request)

    def _verify_callback(self, params):
        """Should be implemented by subclasses to verify the callback"""
        processor = get_payment_processor(self.provider)
        return processor.verify_callback(params)

    def _success_response(self, payment):
        """Generate success response for the payment provider"""
        return HttpResponse(f"OK{payment.id}")


class InitiateRobokassaPaymentView(BasePaymentView):
    provider = 'robokassa'

    def _create_payment(self, user, amount, total_amount):
        return create_robokassa_payment(user, amount, total_amount)


class RobokassaCallbackView(BaseCallbackView):
    provider = 'robokassa'
    ip_whitelist_setting = 'ALLOWED_ROBOKASSA_IPS'

    def _verify_callback(self, params):
        return verify_robokassa_callback(params)


class InitiateYooKassaPaymentView(BasePaymentView):
    provider = 'yookassa'

    def _create_payment(self, user, amount, total_amount):
        return create_yookassa_payment(user, amount, total_amount)


class YooKassaCallbackView(BaseCallbackView):
    provider = 'yookassa'

    def post(self, request):
        try:
            if not self.check_ip_whitelist(request):
                return HttpResponse("Invalid IP", status=403)

            data = json.loads(request.body)
            payment, is_valid = verify_yookassa_callback(data)

            if not payment:
                return HttpResponse("Invalid payment", status=400)

            if is_valid:
                return HttpResponse("OK")
            else:
                return HttpResponse("Invalid payment status", status=400)
        except Exception:
            logger.exception('Error processing YooKassa callback')
            return HttpResponse("Error", status=500)


class InitiateHelekitPaymentView(BasePaymentView):
    provider = 'heleket'

    def _create_payment(self, user, amount, total_amount):
        return create_heleket_payment(user, amount, total_amount)


class HelekitCallbackView(BaseCallbackView):
    provider = 'heleket'
    ip_whitelist_setting = 'ALLOWED_HELEKET_IPS'

    def _verify_callback(self, params):
        return verify_heleket_callback(params)


class PaymentStatusView(View):
    @method_decorator(login_required)
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)
            return JsonResponse({
                'success': True,
                'status': payment.status,
                'amount': float(payment.amount),
                'total_amount': float(payment.total_amount),
                'created_at': payment.created_at.isoformat()
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Платеж не найден'
            }, status=404)

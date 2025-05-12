import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

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
            logger.exception("Error creating payment")
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

        # Direct access to specific settings without any reflection
        whitelist = None
        if self.ip_whitelist_setting == 'ALLOWED_ROBOKASSA_IPS':
            try:
                whitelist = settings.ALLOWED_ROBOKASSA_IPS
            except AttributeError:
                # Setting doesn't exist
                return True
        elif self.ip_whitelist_setting == 'ALLOWED_HELEKET_IPS':
            try:
                whitelist = settings.ALLOWED_HELEKET_IPS
            except AttributeError:
                # Setting doesn't exist
                return True
        else:
            # Unknown whitelist setting
            return True

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
            logger.exception("Error processing payment callback")
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

            # Format decimal amounts to 2 decimal places
            amount = payment.amount
            total_amount = payment.total_amount

            try:
                amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except AttributeError:
                pass

            try:
                total_amount = total_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            except AttributeError:
                pass

            return JsonResponse({
                'success': True,
                'status': payment.status,
                'amount': float(amount),
                'total_amount': float(total_amount),
                'created_at': payment.created_at.isoformat()
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Платеж не найден'
            }, status=404)


class PaymentRequisitesView(TemplateView):
    """View for payment requisites page"""
    template_name = 'payments/requisites.html'


class TestSuccessView(View):
    """
    View for handling test mode payment success redirects.
    This simulates the return from a payment gateway in test mode.
    """

    @method_decorator(login_required)
    def get(self, request):
        payment_id = request.GET.get('payment_id')
        if not payment_id:
            return JsonResponse({'error': 'Отсутствует ID платежа'}, status=400)

        try:
            payment = Payment.objects.get(id=payment_id, user=request.user)

            # Redirect to the dashboard with a success message
            messages.success(request, f"Тестовый платеж на сумму {payment.amount} руб. успешно выполнен!")
            return redirect('accounts:dashboard')

        except Payment.DoesNotExist:
            return JsonResponse({'error': 'Некорректный платеж'}, status=400)

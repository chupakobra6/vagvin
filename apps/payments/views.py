import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Payment
from .services import create_robokassa_payment, verify_robokassa_callback


class PaymentFormView(View):
    @method_decorator(login_required)
    def get(self, request):
        return render(request, 'payments/payment_form.html')


class InitiateRobokassaPaymentView(View):
    @method_decorator(login_required)
    def post(self, request):
        try:
            data = json.loads(request.body) if request.body else request.POST
            amount = float(data.get('amount', 0))

            if amount <= 0:
                return JsonResponse({'error': 'Сумма должна быть положительной'}, status=400)

            payment, payment_url = create_robokassa_payment(request.user, amount)

            return JsonResponse({
                'success': True,
                'payment_url': payment_url,
                'payment_id': payment.id
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)


# TODO: Разобраться насчёт static и проверки ALLOWED_ROBOKASSA_IPS
@method_decorator(csrf_exempt, name='dispatch')
class RobokassaCallbackView(View):
    def get(self, request):
        if request.META.get('REMOTE_ADDR') not in settings.ALLOWED_ROBOKASSA_IPS:
            return HttpResponse("Invalid IP", status=403)

        params = request.GET.dict()
        payment, is_valid = verify_robokassa_callback(params)

        if not payment:
            return HttpResponse("Invalid payment", status=400)

        if is_valid:
            return HttpResponse("OK" + str(payment.id))
        else:
            return HttpResponse("Invalid signature", status=400)

    def post(self, request):
        return self.get(request)


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

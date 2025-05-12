import json
import logging
from decimal import Decimal
from typing import Dict, Any

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_POST

from .forms import AdditionalEmailForm
from .services import UserService
from apps.payments.services import PaymentService

logger = logging.getLogger(__name__)


@login_required
@require_POST
def add_email(request: HttpRequest) -> JsonResponse:
    """API endpoint for adding an additional email"""
    form = AdditionalEmailForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        success, message, emails = UserService.add_additional_email(request.user, email)
        
        if success:
            return JsonResponse({'success': True, 'emails': emails})
        else:
            return JsonResponse({
                'success': False, 
                'message': message
            }, status=400)
    else:
        return JsonResponse({
            'success': False, 
            'message': 'Неверный формат email.'
        }, status=400)


@login_required
@require_POST
def remove_email(request: HttpRequest) -> JsonResponse:
    """API endpoint for removing an additional email"""
    email = request.POST.get('email')
    success, message, emails = UserService.remove_additional_email(request.user, email)
    
    if success:
        return JsonResponse({'success': True, 'emails': emails})
    else:
        return JsonResponse({
            'success': False, 
            'message': message
        }, status=400 if message == "Email not found" else 500)


@login_required
@require_POST
def update_balance(request: HttpRequest) -> JsonResponse:
    """API endpoint for updating user balance"""
    try:
        cost = Decimal(request.POST.get('cost', '0'))
        
        if cost <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'Cost must be positive'
            }, status=400)
            
        success, data = PaymentService.update_balance(request.user, -cost)
        
        if success:
            return JsonResponse({
                'success': True, 
                'new_balance': float(data['new_balance'])
            })
        else:
            return JsonResponse({
                'success': False, 
                'message': data['message']
            }, status=500)
            
    except (ValueError, TypeError):
        logger.exception("Invalid value provided for update_balance")
        return JsonResponse({
            'success': False, 
            'message': 'Invalid cost value'
        }, status=400)


@login_required
@require_POST
def create_payment(request: HttpRequest) -> JsonResponse:
    """API endpoint for creating a payment"""
    try:
        data = json.loads(request.body)
        amount = Decimal(data.get('amount', '0'))
        payment_method = data.get('payment_method', '')
        description = data.get('description', 'Balance refill')
        
        if amount <= 0:
            return JsonResponse({
                'success': False, 
                'message': 'Amount must be positive'
            }, status=400)
            
        if not payment_method:
            return JsonResponse({
                'success': False, 
                'message': 'Payment method is required'
            }, status=400)
            
        # This is a placeholder for future implementation
        # Should be integrated with payment providers like Robokassa, YooKassa, etc.
        return JsonResponse({
            'success': False, 
            'message': 'Not implemented yet'
        }, status=501)
            
    except json.JSONDecodeError:
        logger.exception("Invalid JSON in create_payment request")
        return JsonResponse({
            'success': False, 
            'message': 'Invalid JSON data'
        }, status=400)
    except (ValueError, TypeError):
        logger.exception("Invalid value provided for create_payment")
        return JsonResponse({
            'success': False, 
            'message': 'Invalid amount value'
        }, status=400) 
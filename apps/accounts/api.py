import logging
from typing import Dict, Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from .forms import AdditionalEmailForm
from .services import UserService
from apps.payments.services import PaymentService

logger = logging.getLogger(__name__)


class AddEmailView(LoginRequiredMixin, View):
    """API endpoint for adding an additional email"""
    
    @method_decorator(require_POST)
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
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


class RemoveEmailView(LoginRequiredMixin, View):
    """API endpoint for removing an additional email"""
    
    @method_decorator(require_POST)
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        email = request.POST.get('email')
        success, message, emails = UserService.remove_additional_email(request.user, email)
        
        if success:
            return JsonResponse({'success': True, 'emails': emails})
        else:
            return JsonResponse({
                'success': False, 
                'message': message
            }, status=400 if message == "Email не найден" else 500)
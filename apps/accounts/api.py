import logging
from typing import Dict, Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpRequest
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST

from .forms import AdditionalEmailForm
from .services import UserService

logger = logging.getLogger(__name__)


class BaseApiView(LoginRequiredMixin, View):
    """Base class for API views"""
    
    def json_error(self, message: str, status: int = 400) -> JsonResponse:
        """Return a standardized error response"""
        return JsonResponse({
            'success': False,
            'message': message
        }, status=status)
    
    def json_success(self, data: Dict[str, Any]) -> JsonResponse:
        """Return a standardized success response"""
        response = {'success': True}
        response.update(data)
        return JsonResponse(response)


class AddEmailView(BaseApiView):
    """API endpoint for adding an additional email"""
    
    @method_decorator(require_POST)
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        form = AdditionalEmailForm(request.POST)
        if not form.is_valid():
            return self.json_error('Неверный формат email.')
            
        email = form.cleaned_data['email']
        success, message, emails = UserService.add_additional_email(request.user, email)
        
        if success:
            return self.json_success({'emails': emails})
        return self.json_error(message)


class RemoveEmailView(BaseApiView):
    """API endpoint for removing an additional email"""
    
    @method_decorator(require_POST)
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        email = request.POST.get('email')
        success, message, emails = UserService.remove_additional_email(request.user, email)
        
        if success:
            return self.json_success({'emails': emails})
        
        status = 400 if message == "Email не найден" else 500
        return self.json_error(message, status)
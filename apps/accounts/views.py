import logging
from typing import Dict, Any
import json
import re

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.payments.models import Payment
from apps.payments.services import PaymentService
from apps.reports.models import Query
from apps.reports.services import (
    AutotekaService,
    CarfaxService,
    VinhistoryService,
    AuctionService,
    AvitoService
)
from .forms import RegistrationForm, ForgotPasswordForm, LoginForm
from .services import UserService

logger = logging.getLogger(__name__)


class LoginView(FormView):
    """User authentication view"""
    template_name = 'accounts/login.html'
    form_class = LoginForm
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().get(request, *args, **kwargs)
        
    def form_valid(self, form: LoginForm) -> HttpResponse:
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        user = UserService.authenticate_user(username, password)
        if user is not None:
            login(self.request, user)
            return redirect('accounts:dashboard')
        return self.form_invalid(form)


class LogoutView(View):
    """User logout view"""
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        logout(request)
        return redirect('pages:home')


class RegisterView(FormView):
    """User registration view"""
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = '/accounts/login/'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['referral_code'] = self.request.GET.get('ref')
        return context

    def form_valid(self, form: RegistrationForm) -> HttpResponse:
        email = form.cleaned_data['email']
        referral_code = self.request.GET.get('ref')
        
        success, message, user = UserService.register_user(email, referral_code)
        
        if success:
            messages.success(self.request, message)
            return super().form_valid(form)
        
        messages.error(self.request, message)
        return self.form_invalid(form)


class ForgotPasswordView(FormView):
    """Password reset request view"""
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form: ForgotPasswordForm) -> HttpResponse:
        email = form.cleaned_data['email']
        
        success, message = UserService.reset_password(email)
        
        if success:
            messages.success(self.request, message)
            return super().form_valid(form)
        
        messages.error(self.request, message)
        return redirect('accounts:login') if 'wait' in message.lower() else self.form_invalid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard view"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        
        user_data = UserService.get_user_data(user)
        context['user_data'] = user_data
        
        payment_stats = PaymentService.get_user_payments_stats(user)
        
        context['payments_count'] = payment_stats.get('successful_count', 0)
        
        total_amount = payment_stats.get('successful_total', 0)
        if total_amount:
            from decimal import Decimal, ROUND_HALF_UP
            total_amount = Decimal(str(total_amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        context['total_amount'] = total_amount
        
        payments = Payment.objects.filter(
            user=user
        ).order_by('-created_at')
        
        last_payment = payments.filter(status='success').first()
        context['last_payment'] = last_payment
        
        context['payments'] = payments[:10]
        
        user_queries = Query.objects.filter(user=user).order_by('-created_at')[:20]
        context['user_queries'] = user_queries
        
        return context


# View for handling the unified check request from the dashboard
# @method_decorator(csrf_exempt, name='dispatch') # CSRF should be handled by middleware for authenticated POST requests
class UnifiedCheckView(LoginRequiredMixin, View):
    """API endpoint for performing a unified check across multiple services."""
    
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Handle POST requests with VIN."""
        try:
            data = json.loads(request.body)
            vin = data.get('vin')
            if not vin:
                return JsonResponse({"error": "VIN не предоставлен"}, status=400)
            
            # Basic VIN validation (length, pattern can be stricter)
            vin = vin.strip().upper()
            if len(vin) != 17 or not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
                 return JsonResponse({"error": "Некорректный формат VIN"}, status=400)

            logger.info(f"User {request.user.username} requested unified check for VIN: {vin}")

            # Perform checks using services from reports app
            # We run these sequentially for simplicity, could be parallelized later if needed
            autoteka_result = AutotekaService.check(vin, 'vin') # Assume VIN check for Autoteka here
            carfax_result = CarfaxService.check(vin)
            vinhistory_result = VinhistoryService.check(vin)
            auction_result = AuctionService.check(vin)
            
            # Save the query for the user's history
            try:
                Query.objects.create(
                    user=request.user,
                    vin=vin,
                    query_type='unified' # Use a specific type for unified checks
                )
                logger.info(f"Saved unified query for user {request.user.username}, VIN {vin}")
            except Exception:
                # Log failure but don't block returning results to user
                logger.exception(f"Failed to save unified query history for user {request.user.username}, VIN {vin}")

            # Aggregate results
            results = {
                "autoteka": autoteka_result,
                "carfax": carfax_result,
                "vinhistory": vinhistory_result,
                "auction": auction_result
            }
            
            return JsonResponse(results)

        except json.JSONDecodeError:
            logger.warning("Invalid JSON received for unified check")
            return JsonResponse({"error": "Некорректный формат запроса"}, status=400)
        except Exception:
            logger.exception(f"Unexpected error during unified check for user {request.user.username}")
            return JsonResponse({"error": "Внутренняя ошибка сервера при проверке"}, status=500)

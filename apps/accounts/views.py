import logging
from typing import Dict, Any, Optional

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from .forms import RegistrationForm, ForgotPasswordForm, LoginForm
from .models import User
from .services import UserService
from .utils import generate_password, send_registration_email, send_password_reset_email

logger = logging.getLogger(__name__)


def login_view(request: HttpRequest) -> HttpResponse:
    """View for user login"""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            user = UserService.authenticate_user(username, password)
            if user is not None:
                login(request, user)
                return redirect('accounts:dashboard')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
    """View for user logout"""
    logout(request)
    return redirect('pages:home')


class RegisterView(FormView):
    """View for user registration"""
    template_name = 'accounts/register.html'
    form_class = RegistrationForm
    success_url = '/accounts/login/'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['referral_code'] = self.request.GET.get('ref')
        return context

    def form_valid(self, form) -> HttpResponse:
        email = form.cleaned_data['email']
        referral_code = self.request.GET.get('ref')
        
        success, message, user = UserService.register_user(email, referral_code)
        
        if success:
            messages.success(self.request, message)
            return super().form_valid(form)
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)


class ForgotPasswordView(FormView):
    """View for password reset"""
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form) -> HttpResponse:
        email = form.cleaned_data['email']
        
        success, message = UserService.reset_password(email)
        
        if success:
            messages.success(self.request, message)
            return super().form_valid(form)
        else:
            messages.error(self.request, message)
            return redirect('accounts:login') if 'wait' in message.lower() else self.form_invalid(form)


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """View for user dashboard"""
    from apps.payments.services import PaymentService
    
    # Initialize context
    context = {}
    
    # Get user data first (it should take precedence)
    user_data = UserService.get_user_data(request.user)
    context['user_data'] = user_data
    
    # Get payment stats, but don't override existing user_data fields
    user_payment_stats = PaymentService.get_user_payments_stats(request.user)
    
    # Remove any keys that might conflict with user_data
    user_payment_stats.pop('balance', None)
    
    # Update context with payment stats
    context.update(user_payment_stats)
    
    return render(request, 'accounts/dashboard.html', context)

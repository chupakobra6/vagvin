import logging
from typing import Dict, Any

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, View, TemplateView

from .forms import RegistrationForm, ForgotPasswordForm, LoginForm
from .services import UserService

logger = logging.getLogger(__name__)


class LoginView(FormView):
    """View for user login"""
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
    """View for user logout"""
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        logout(request)
        return redirect('pages:home')


class RegisterView(FormView):
    """View for user registration"""
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
        else:
            messages.error(self.request, message)
            return self.form_invalid(form)


class ForgotPasswordView(FormView):
    """View for password reset"""
    template_name = 'accounts/forgot_password.html'
    form_class = ForgotPasswordForm
    success_url = reverse_lazy('accounts:login')

    def form_valid(self, form: ForgotPasswordForm) -> HttpResponse:
        email = form.cleaned_data['email']
        
        success, message = UserService.reset_password(email)
        
        if success:
            messages.success(self.request, message)
            return super().form_valid(form)
        else:
            messages.error(self.request, message)
            return redirect('accounts:login') if 'wait' in message.lower() else self.form_invalid(form)


class DashboardView(LoginRequiredMixin, TemplateView):
    """View for user dashboard"""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        from apps.payments.services import PaymentService
        
        # Get user data first (it should take precedence)
        user_data = UserService.get_user_data(self.request.user)
        context['user_data'] = user_data
        
        # Get payment stats, but don't override existing user_data fields
        user_payment_stats = PaymentService.get_user_payments_stats(self.request.user)
        
        # Remove any keys that might conflict with user_data
        user_payment_stats.pop('balance', None)
        
        # Update context with payment stats
        context.update(user_payment_stats)
        
        return context

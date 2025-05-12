import logging
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views.generic import TemplateView, View

from .services import PageViewService

logger = logging.getLogger(__name__)


class BasePageView(TemplateView):
    """Base view for static pages with shared functionality"""
    page_name: str = "page"
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Log the page view and render the template"""
        PageViewService.log_page_view(self.page_name)
        return super().get(request, *args, **kwargs)


class HomeView(BasePageView):
    """Render the home page."""
    template_name = 'pages/home.html'
    page_name = 'home'


class AboutView(BasePageView):
    """Render the about page."""
    template_name = 'pages/about.html'
    page_name = 'about'


class FaqView(BasePageView):
    """Render the FAQ page."""
    template_name = 'pages/faq.html'
    page_name = 'FAQ'


class RequisitesView(BasePageView):
    """Render the requisites page."""
    template_name = 'pages/requisites.html'
    page_name = 'requisites'


class PrivacyPolicyView(BasePageView):
    """Render the privacy policy page."""
    template_name = 'pages/privacy_policy.html'
    page_name = 'privacy policy'


class PaymentRulesView(BasePageView):
    """Render the payment rules page."""
    template_name = 'pages/payment_rules.html'
    page_name = 'payment rules'


class BaseRedirectView(View):
    """Base view for redirect pages with shared functionality"""
    redirect_to: str = ""
    redirect_name: str = "page"
    
    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Log the redirect and perform the redirect"""
        logger.debug(f"Redirecting to {self.redirect_name}")
        return redirect(self.redirect_to)


class ExamplesRedirectView(BaseRedirectView):
    """Redirect to the examples page in the reports app."""
    redirect_to = 'reports:examples'
    redirect_name = 'reports examples page'


class ReviewsRedirectView(BaseRedirectView):
    """Redirect to the reviews listing page in the reviews app."""
    redirect_to = 'reviews:list'
    redirect_name = 'reviews listing page'


class DashboardRedirectView(BaseRedirectView):
    """Redirect to the user dashboard in the accounts app."""
    redirect_to = 'accounts:dashboard'
    redirect_name = 'user dashboard'

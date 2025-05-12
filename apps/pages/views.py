import logging

from django.shortcuts import redirect
from django.views.generic import TemplateView, View

logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    """Render the home page."""
    template_name = 'pages/home.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering home page")
        return super().get(request, *args, **kwargs)


class AboutView(TemplateView):
    """Render the about page."""
    template_name = 'pages/about.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering about page")
        return super().get(request, *args, **kwargs)


class FaqView(TemplateView):
    """Render the FAQ page."""
    template_name = 'pages/faq.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering FAQ page")
        return super().get(request, *args, **kwargs)


class RequisitesView(TemplateView):
    """Render the requisites page."""
    template_name = 'pages/requisites.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering requisites page")
        return super().get(request, *args, **kwargs)


class PrivacyPolicyView(TemplateView):
    """Render the privacy policy page."""
    template_name = 'pages/privacy_policy.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering privacy policy page")
        return super().get(request, *args, **kwargs)


class PaymentRulesView(TemplateView):
    """Render the payment rules page."""
    template_name = 'pages/payment_rules.html'

    def get(self, request, *args, **kwargs):
        logger.debug("Rendering payment rules page")
        return super().get(request, *args, **kwargs)


class ExamplesRedirectView(View):
    """Redirect to the examples page in the reports app."""

    def get(self, request, *args, **kwargs):
        logger.debug("Redirecting to reports examples page")
        return redirect('reports:examples')

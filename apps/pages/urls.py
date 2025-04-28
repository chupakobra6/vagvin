from django.urls import path

from .views import (
    home_view, about_view, faq_view, requisites_view,
    examples_view, privacy_policy_view, payment_rules_view
)

app_name = 'pages'

urlpatterns = [
    path('', home_view, name='home'),
    path('about/', about_view, name='about'),
    path('faq/', faq_view, name='faq'),
    path('requisites/', requisites_view, name='requisites'),
    path('examples/', examples_view, name='examples'),
    path('privacy-policy/', privacy_policy_view, name='privacy_policy'),
    path('payment-rules/', payment_rules_view, name='payment_rules'),
]

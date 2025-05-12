from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('faq/', views.FaqView.as_view(), name='faq'),
    path('requisites/', views.RequisitesView.as_view(), name='requisites'),
    path('examples/', views.ExamplesRedirectView.as_view(), name='examples'),
    # TODO: Add review redirect
    # TODO: Add dashboard redirect
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('payment-rules/', views.PaymentRulesView.as_view(), name='payment_rules'),
]

from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    # Static pages
    path('', views.HomeView.as_view(), name='home'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('faq/', views.FaqView.as_view(), name='faq'),
    path('requisites/', views.RequisitesView.as_view(), name='requisites'),
    path('privacy-policy/', views.PrivacyPolicyView.as_view(), name='privacy_policy'),
    path('payment-rules/', views.PaymentRulesView.as_view(), name='payment_rules'),
    
    # Redirects to other app pages
    path('examples/', views.ExamplesRedirectView.as_view(), name='examples'),
    path('reviews/', views.ReviewsRedirectView.as_view(), name='reviews'),
    path('dashboard/', views.DashboardRedirectView.as_view(), name='dashboard'),
]

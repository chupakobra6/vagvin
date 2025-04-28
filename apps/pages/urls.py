from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'pages'

urlpatterns = [
    # Page routes
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('examples/', views.examples_view, name='examples'),
    path('terms-of-service/', views.terms_of_service, name='terms_of_service'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('payment-rules/', views.payment_rules_view, name='payment_rules'),
    path('requisites/', views.requisites_view, name='requisites'),
    
    # API routes - support both GET and POST methods
    # We use the _view functions since they're already CSRF-exempted for POST
    path('api/check/autoteka/', csrf_exempt(views.check_autoteka_view), name='api_check_autoteka'),
    path('api/check/carfax-autocheck/', csrf_exempt(views.check_carfax_view), name='api_check_carfax_autocheck'),
    path('api/check/vinhistory/', csrf_exempt(views.check_vinhistory_view), name='api_check_vinhistory'),
    path('api/check/auction/', csrf_exempt(views.check_auction_view), name='api_check_auction'),
    
    # Utility routes
    path('get_messages/', views.get_messages_view, name='get_messages'),
    
    # Debug routes - admin only
    path('debug/api/', views.debug_api_view, name='debug_api'),
]

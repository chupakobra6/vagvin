from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Страница оплаты
    path('', views.PaymentFormView.as_view(), name='payment_form'),
    
    # Маршруты для Robokassa
    path('robokassa/initiate/', views.InitiateRobokassaPaymentView.as_view(), name='robokassa_initiate'),
    path('robokassa/callback/', views.RobokassaCallbackView.as_view(), name='robokassa_callback'),
    path('status/<int:payment_id>/', views.PaymentStatusView.as_view(), name='payment_status'),
] 
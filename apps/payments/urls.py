from django.urls import path

from . import views

app_name = 'payments'

urlpatterns = [
    # Payment pages
    path('requisites/', views.PaymentRequisitesView.as_view(), name='requisites'),

    # Robokassa routes
    path('robokassa/initiate/', views.InitiateRobokassaPaymentView.as_view(), name='robokassa_initiate'),
    path('robokassa/callback/', views.RobokassaCallbackView.as_view(), name='robokassa_callback'),

    # YooKassa routes
    path('yookassa/initiate/', views.InitiateYooKassaPaymentView.as_view(), name='yookassa_initiate'),
    path('yookassa/callback/', views.YooKassaCallbackView.as_view(), name='yookassa_callback'),

    # Heleket routes
    path('heleket/initiate/', views.InitiateHelekitPaymentView.as_view(), name='heleket_initiate'),
    path('heleket/callback/', views.HelekitCallbackView.as_view(), name='heleket_callback'),

    # Payment status
    path('status/<int:payment_id>/', views.PaymentStatusView.as_view(), name='payment_status'),

    # Test mode routes
    path('test-success/', views.TestSuccessView.as_view(), name='test_success'),
]

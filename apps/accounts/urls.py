from django.urls import path
from django.urls import reverse_lazy

from . import forms
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # API endpoints
    path('api/add-email/', views.add_email, name='add_email'),
    path('api/remove-email/', views.remove_email, name='remove_email'),
    path('api/update-balance/', views.update_balance, name='update_balance'),
]

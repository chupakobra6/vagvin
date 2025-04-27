from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import LoginForm
from .views import (
    RegisterView,
    dashboard,
    ForgotPasswordView,
    add_email,
    remove_email,
    update_balance
)

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(
        template_name='accounts/login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),

    # Dashboard
    path('dashboard/', dashboard, name='dashboard'),

    # API endpoints
    path('api/add-email/', add_email, name='add_email'),
    path('api/remove-email/', remove_email, name='remove_email'),
    path('api/update-balance/', update_balance, name='update_balance'),
]

from django.urls import path

from . import views
from . import api

app_name = 'accounts'

# Web views
web_urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
]

# API endpoints
api_urlpatterns = [
    path('api/add-email/', api.add_email, name='add_email'),
    path('api/remove-email/', api.remove_email, name='remove_email'),
    path('api/update-balance/', api.update_balance, name='update_balance'),
    path('api/create-payment/', api.create_payment, name='create_payment'),
]

# All URLs
urlpatterns = web_urlpatterns + api_urlpatterns

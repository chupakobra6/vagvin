from django.urls import path

from . import views
from . import api

app_name = 'accounts'

# Web views
web_urlpatterns = [
    # Authentication
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot_password'),

    # Dashboard
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
]

# API endpoints
api_urlpatterns = [
    path('api/add-email/', api.AddEmailView.as_view(), name='add_email'),
    path('api/remove-email/', api.RemoveEmailView.as_view(), name='remove_email'),
]

# All URLs
urlpatterns = web_urlpatterns + api_urlpatterns

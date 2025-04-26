from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('faq/', views.faq_view, name='faq'),
    path('requisites/', views.requisites_view, name='requisites'),
    path('examples/', views.examples_view, name='examples'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('login/', views.login_view, name='login'),
]

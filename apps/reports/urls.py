from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Get user queries
    path('api/user-queries/', views.user_queries, name='user_queries'),
    # Create query and update balance
    path('api/create-query/', views.create_query, name='create_query'),
]
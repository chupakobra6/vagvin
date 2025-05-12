from django.urls import path

from . import views

app_name = 'reviews'

urlpatterns = [
    path('list/', views.ReviewListView.as_view(), name='list'),
    path('widget/', views.ReviewWidgetView.as_view(), name='widget'),
]

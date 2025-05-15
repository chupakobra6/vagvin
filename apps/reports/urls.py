from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from . import views

app_name = 'reports'

urlpatterns = [
    # Examples page
    path('examples/', views.ExamplesView.as_view(), name='examples'),

    # Vehicle check endpoints
    path('api/check/autoteka/', views.AutotekaCheckView.as_view(), name='api_check_autoteka'),
    path('api/check/carfax-autocheck/', views.CarfaxCheckView.as_view(), name='api_check_carfax_autocheck'),
    path('api/check/vinhistory/', views.VinhistoryCheckView.as_view(), name='api_check_vinhistory'),
    path('api/check/auction/', views.AuctionCheckView.as_view(), name='api_check_auction'),
    
    # Recent website queries endpoint
    path('api/recent-queries/', views.RecentQueriesView.as_view(), name='recent_queries'),
]
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin site URL
    path('admin/', admin.site.urls),

    # App-specific URL patterns come first
    path('accounts/', include('apps.accounts.urls')),
    path('payments/', include('apps.payments.urls')),
    path('reports/', include('apps.reports.urls')), 
    path('reviews/', include('apps.reviews.urls')),
    
    # Main pages URLs (homepage and static pages) - should be last to catch all other URLs
    path('', include('apps.pages.urls')),

    # Redirects for backward compatibility
    path('login/', RedirectView.as_view(pattern_name='accounts:login', permanent=True)),
    path('register/', RedirectView.as_view(pattern_name='accounts:register', permanent=True)),
]

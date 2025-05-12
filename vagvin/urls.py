from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    # Admin site URL
    path('admin/', admin.site.urls),

    # Main pages URLs (homepage and static pages)
    path('', include('apps.pages.urls')),

    # User accounts (authentication, profile, etc.)
    path('accounts/', include('apps.accounts.urls')),

    # Payment-related URLs
    path('payments/', include('apps.payments.urls')),

    # Reports and query history URLs
    path('reports/', include('apps.reports.urls')),

    # Reviews URLs
    path('reviews/', include('apps.reviews.urls')),

    # Redirects for backward compatibility
    path('login/', RedirectView.as_view(pattern_name='accounts:login', permanent=True)),
    path('register/', RedirectView.as_view(pattern_name='accounts:register', permanent=True)),
]

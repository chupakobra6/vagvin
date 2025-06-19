from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django_prometheus import exports
from . import views

urlpatterns = [
    # Admin site URL
    path("admin/", admin.site.urls),
    # App-specific URL patterns come first
    path("accounts/", include("apps.accounts.urls")),
    path("payments/", include("apps.payments.urls")),
    path("reports/", include("apps.reports.urls")),
    path("reviews/", include("apps.reviews.urls")),
    # Metrics endpoint for Prometheus
    path(
        "metrics/",
        exports.ExportToDjangoView,
        name="prometheus-django-metrics",
    ),
    # Update custom metrics endpoint
    path(
        "update-metrics/",
        views.update_metrics,
        name="update-metrics",
    ),
    # Main pages URLs (homepage and static pages) - should be last to catch all other URLs
    path("", include("apps.pages.urls")),
    # Redirects for backward compatibility
    path("login/", RedirectView.as_view(pattern_name="accounts:login", permanent=True)),
    path(
        "register/",
        RedirectView.as_view(pattern_name="accounts:register", permanent=True),
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

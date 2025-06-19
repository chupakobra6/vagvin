import time
import logging
from typing import Callable
from django.http import HttpRequest, HttpResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from django.contrib.auth import get_user_model
from apps.payments.models import Payment
from apps.reports.models import Query
from apps.reviews.models import Review

logger = logging.getLogger(__name__)

# Custom Prometheus metrics
user_registrations_total = Counter(
    'django_user_registrations_total',
    'Total number of user registrations'
)

user_logins_total = Counter(
    'django_user_logins_total', 
    'Total number of user logins'
)

active_users_gauge = Gauge(
    'django_active_users',
    'Number of users who logged in in the last 24 hours'
)

database_objects_gauge = Gauge(
    'django_database_objects_total',
    'Total number of objects in database',
    ['model']
)

payments_total = Counter(
    'django_payments_total',
    'Total number of payments',
    ['status']
)

reports_generated_total = Counter(
    'django_reports_generated_total',
    'Total number of reports generated'
)

reviews_total = Counter(
    'django_reviews_total',
    'Total number of reviews',
    ['rating']
)

request_duration_histogram = Histogram(
    'django_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint', 'status_code']
)


class PrometheusMonitoringMiddleware:
    """Custom middleware to collect additional metrics."""
    
    def __init__(self, get_response: Callable):
        self.get_response = get_response
        
    def __call__(self, request: HttpRequest) -> HttpResponse:
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Record request duration
        duration = time.time() - start_time
        endpoint = self._get_endpoint_name(request)
        request_duration_histogram.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=response.status_code
        ).observe(duration)
        
        return response
    
    def _get_endpoint_name(self, request: HttpRequest) -> str:
        """Get simplified endpoint name from request path."""
        path = request.path.strip('/')
        if not path:
            return 'home'
        elif path.startswith('admin'):
            return 'admin'
        elif path.startswith('accounts'):
            return 'accounts'
        elif path.startswith('payments'):
            return 'payments'
        elif path.startswith('reports'):
            return 'reports'
        elif path.startswith('reviews'):
            return 'reviews'
        elif path == 'metrics':
            return 'metrics'
        else:
            return 'other'


def update_database_metrics():
    """Update database-related metrics."""
    try:
        User = get_user_model()
        
        # Update model counts
        database_objects_gauge.labels(model='User').set(User.objects.count())
        database_objects_gauge.labels(model='Payment').set(Payment.objects.count())
        database_objects_gauge.labels(model='Query').set(Query.objects.count())
        database_objects_gauge.labels(model='Review').set(Review.objects.count())
        
        # Update active users (users who logged in in the last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        yesterday = timezone.now() - timedelta(days=1)
        active_count = User.objects.filter(last_login__gte=yesterday).count()
        active_users_gauge.set(active_count)
        
        # Update payment status counts
        for status_choice in Payment.STATUS_CHOICES:
            status = status_choice[0]
            count = Payment.objects.filter(status=status).count()
            payments_total.labels(status=status)._value._value = count
        
        # Update review ratings counts
        for rating in range(1, 6):  # Ratings 1-5
            count = Review.objects.filter(rating=rating).count()
            reviews_total.labels(rating=str(rating))._value._value = count
            
        # Update reports count
        reports_generated_total._value._value = Query.objects.count()
        
    except Exception as e:
        logger.exception(f"Error updating database metrics: {e}")


def record_user_registration():
    """Record a user registration event."""
    user_registrations_total.inc()


def record_user_login():
    """Record a user login event."""
    user_logins_total.inc()


def record_payment(status: str):
    """Record a payment with given status."""
    payments_total.labels(status=status).inc()


def record_report_generation():
    """Record a report generation event."""
    reports_generated_total.inc()


def record_review(rating: int):
    """Record a review with given rating."""
    reviews_total.labels(rating=str(rating)).inc() 
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .monitoring import update_database_metrics


@csrf_exempt
@require_http_methods(["GET", "POST"])
def update_metrics(request):
    """Update custom database metrics."""
    try:
        update_database_metrics()
        return JsonResponse({"status": "success", "message": "Metrics updated"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500) 
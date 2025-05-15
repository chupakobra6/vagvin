from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.contrib.auth import get_user_model
from .models import Query
from .services import (
    AutotekaService,
    CarfaxService,
    VinhistoryService,
    AuctionService,
    AvitoService,
    ExamplesService
)

User = get_user_model()
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class AutotekaCheckView(View):
    """API endpoint for checking vehicle information in Autoteka."""
    
    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Autoteka check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data) -> JsonResponse:
        """Process the check request."""
        logger.info("Autoteka check request received")
        
        input_type = None
        input_value = None
        
        if data.get('vin'):
            input_type = 'vin'
            input_value = data.get('vin')
            # Save query to database
            save_website_query(input_value, 'autoteka')
        elif data.get('regNumber'):
            input_type = 'regNumber'
            input_value = data.get('regNumber')
            # Save query to database with registration number as VIN
            save_website_query(input_value, 'autoteka_reg')
        elif data.get('avitoUrl'):
            avito_id = AvitoService.extract_id(data.get('avitoUrl'))
            if avito_id:
                input_type = 'itemId'
                input_value = avito_id
                # Save query to database with Avito ID as VIN
                save_website_query(f"AVITO-{avito_id}", 'autoteka_avito')
            else:
                logger.warning(f"Invalid Avito URL provided: {data.get('avitoUrl')}")
                return JsonResponse({"error": "Невозможно извлечь ID объявления из предоставленной ссылки Avito"}, status=400)
        else:
            logger.warning("Missing required parameters for Autoteka check")
            return JsonResponse({"error": "Необходимо указать VIN, регистрационный номер или ссылку на Avito"}, status=400)
        
        result = AutotekaService.check(input_value, input_type)
        
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class CarfaxCheckView(View):
    """API endpoint for checking vehicle information in Carfax/Autocheck."""
    
    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Carfax check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data) -> JsonResponse:
        """Process the check request."""
        logger.info("Carfax/Autocheck check request received")
        
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Carfax check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Save query to database
        save_website_query(vin, 'carfax')
        
        result = CarfaxService.check(vin)
        
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class VinhistoryCheckView(View):
    """API endpoint for checking vehicle information in Vinhistory."""
    
    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Vinhistory check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data) -> JsonResponse:
        """Process the check request."""
        logger.info("Vinhistory check request received")
        
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Vinhistory check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Save query to database
        save_website_query(vin, 'vinhistory')
        
        result = VinhistoryService.check(vin)
        
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class AuctionCheckView(View):
    """API endpoint for checking vehicle auction history."""
    
    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Auction check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data) -> JsonResponse:
        """Process the check request."""
        logger.info("Auction check request received")
        
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Auction check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Save query to database
        save_website_query(vin, 'auction')
        
        result = AuctionService.check(vin)
        
        return JsonResponse(result)


class ExamplesView(TemplateView):
    """Render the examples page with all available example sections."""
    template_name = 'reports/examples.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add data for examples page."""
        context = super().get_context_data(**kwargs)
        
        context.update({
            'sections': ExamplesService.get_all_sections(),
            'recent_queries': ExamplesService.get_recent_queries(),
            'telegram_bot': 'Data_ViN_PR_bot',
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        logger.debug("Rendering examples page")
        return super().get(request, *args, **kwargs)


class RecentQueriesView(View):
    """API endpoint for getting recent website queries."""

    def get(self, request, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        try:
            limit = int(request.GET.get('limit', 10))
        except ValueError:
            limit = 10
        
        queries = ExamplesService.get_recent_queries(limit=limit)
        # Return JsonResponse consistent with other API views used by JS
        return JsonResponse(queries, safe=False)


# Helper function to save a query from website API checks
def save_website_query(vin: str, query_type_value: str) -> None:
    """
    Save a query from website checks without authentication.
    
    Args:
        vin: Vehicle identification number
        query_type_value: Type of check (autoteka, carfax, etc.) formerly 'tip'
    """
    try:
        # Try to get a "website" user or use the first superuser as a fallback
        website_user = User.objects.filter(username='website').first()
        if not website_user:
            website_user = User.objects.filter(is_superuser=True).first()
        
        if website_user:
            # Create a query without cost (free check from website)
            Query.objects.create(
                user=website_user,
                vin=vin.upper(),
                query_type=query_type_value
            )
            logger.info(f"Saved website query for VIN {vin}, type {query_type_value}")
        else:
            logger.warning("Could not save website query - no suitable user found")
    except Exception:
        logger.exception("Failed to save website query")

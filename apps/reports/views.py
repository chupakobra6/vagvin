from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Query
from .serializers import QuerySerializer
from .utils import create_query_and_update_balance
from .services import (
    AutotekaService,
    CarfaxService,
    VinhistoryService,
    AuctionService,
    extract_avito_id,
    ExamplesService
)

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_queries(request):
    """
    Get user query history.
    Returns the last 50 queries for the authenticated user.
    """
    queries = Query.objects.filter(user=request.user).order_by('-created_at')[:50]
    serializer = QuerySerializer(queries, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_query(request):
    """
    Create a new query and update user balance.
    
    Required POST parameters:
    - vin: Vehicle Identification Number
    - tip: Report type
    
    Optional parameters:
    - marka: Car brand/model
    - lang: Report language (default: 'ru')
    - cost: Cost of the report (default: 0)
    """
    vin = request.data.get('vin')
    tip = request.data.get('tip', 'basic')
    marka = request.data.get('marka', '')
    lang = request.data.get('lang', 'ru')
    cost = request.data.get('cost', 0)
    
    if not vin:
        return Response({'error': 'VIN номер обязателен'}, status=status.HTTP_400_BAD_REQUEST)
    
    query, success = create_query_and_update_balance(
        user=request.user,
        vin=vin,
        marka=marka,
        tip=tip,
        lang=lang,
        cost=cost
    )
    
    if not success:
        return Response(
            {'error': 'Недостаточно средств для выполнения запроса'}, 
            status=status.HTTP_402_PAYMENT_REQUIRED
        )
    
    serializer = QuerySerializer(query)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_exempt, name='dispatch')
class AutotekaCheckView(View):
    """API endpoint for checking vehicle information in Autoteka."""
    
    def get(self, request, *args, **kwargs):
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs):
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Autoteka check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data):
        logger.info("Autoteka check request received")
        
        # Determine input type and value
        input_type = None
        input_value = None
        
        if data.get('vin'):
            input_type = 'vin'
            input_value = data.get('vin')
        elif data.get('regNumber'):
            input_type = 'regNumber'
            input_value = data.get('regNumber')
        elif data.get('avitoUrl'):
            avito_id = extract_avito_id(data.get('avitoUrl'))
            if avito_id:
                input_type = 'itemId'
                input_value = avito_id
            else:
                logger.warning(f"Invalid Avito URL provided: {data.get('avitoUrl')}")
                return JsonResponse({"error": "Невозможно извлечь ID объявления из предоставленной ссылки Avito"}, status=400)
        else:
            logger.warning("Missing required parameters for Autoteka check")
            return JsonResponse({"error": "Необходимо указать VIN, регистрационный номер или ссылку на Avito"}, status=400)
        
        # Call the service to perform the check
        result = AutotekaService.check(input_value, input_type)
        
        # Return the result
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class CarfaxCheckView(View):
    """API endpoint for checking vehicle information in Carfax/Autocheck."""
    
    def get(self, request, *args, **kwargs):
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs):
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Carfax check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data):
        logger.info("Carfax/Autocheck check request received")
        
        # Get VIN from request
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Carfax check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Call the service to perform the check
        result = CarfaxService.check(vin)
        
        # Return the result
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class VinhistoryCheckView(View):
    """API endpoint for checking vehicle information in Vinhistory."""
    
    def get(self, request, *args, **kwargs):
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs):
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Vinhistory check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data):
        logger.info("Vinhistory check request received")
        
        # Get VIN from request
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Vinhistory check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Call the service to perform the check
        result = VinhistoryService.check(vin)
        
        # Return the result
        return JsonResponse(result)


@method_decorator(csrf_exempt, name='dispatch')
class AuctionCheckView(View):
    """API endpoint for checking vehicle auction history."""
    
    def get(self, request, *args, **kwargs):
        return self._process_request(request.GET)
    
    def post(self, request, *args, **kwargs):
        try:
            return self._process_request(request.POST)
        except Exception:
            logger.exception("Error parsing POST data in Auction check")
            return JsonResponse({"error": "Invalid request data"}, status=400)
    
    def _process_request(self, data):
        logger.info("Auction check request received")
        
        # Get VIN from request
        vin = data.get('vin')
        
        if not vin:
            logger.warning("Missing VIN parameter for Auction check")
            return JsonResponse({"error": "Необходимо указать VIN автомобиля"}, status=400)
        
        # Call the service to perform the check
        result = AuctionService.check(vin)
        
        # Return the result
        return JsonResponse(result)


class ExamplesView(TemplateView):
    """Render the examples page with all available example sections."""
    template_name = 'reports/examples.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add data for examples page using the ExamplesService
        context.update({
            'sections': ExamplesService.get_all_sections(),
            'telegram_bot': 'Data_ViN_PR_bot',
        })
        
        return context
    
    def get(self, request, *args, **kwargs):
        logger.debug("Rendering examples page")
        return super().get(request, *args, **kwargs)

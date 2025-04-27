from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Query
from .serializers import QuerySerializer
from .utils import create_query_and_update_balance


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

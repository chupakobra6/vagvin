from decimal import Decimal
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import Query

User = get_user_model()


@transaction.atomic
def create_query_and_update_balance(user, vin, marka='', tip='basic', lang='ru', cost=0):
    """
    Create a new query record and update the user's balance.
    
    Args:
        user: User instance
        vin: Vehicle Identification Number
        marka: Car brand/model
        tip: Report type
        lang: Report language
        cost: Cost of the report
        
    Returns:
        tuple: (query_instance, success_bool)
    """
    # Convert cost to Decimal if it's not already
    if not isinstance(cost, Decimal):
        cost = Decimal(str(cost))
    
    # Check if user has enough balance
    if user.balance < cost:
        # Check if user has available overdraft
        if user.balance + user.overdraft < cost:
            return None, False
    
    # Create query record
    query = Query.objects.create(
        user=user,
        vin=vin,
        marka=marka,
        tip=tip,
        lang=lang,
        cost=cost
    )
    
    # Update user balance
    user.balance = max(Decimal('0'), user.balance - cost)
    user.save(update_fields=['balance'])
    
    return query, True


def get_user_queries(user, limit=50):
    """
    Get the most recent queries for a user.
    
    Args:
        user: User instance
        limit: Maximum number of queries to return
        
    Returns:
        QuerySet: User's queries
    """
    return Query.objects.filter(user=user).order_by('-date_time')[:limit] 
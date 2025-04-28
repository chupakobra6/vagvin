import logging
from decimal import Decimal
from typing import Tuple, Dict, Any, Optional

from django.db import transaction
from django.db.models import F

from .models import User

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment-related operations for user accounts"""
    
    @classmethod
    @transaction.atomic
    def update_balance(cls, user: User, amount: Decimal) -> Tuple[bool, Dict[str, Any]]:
        """
        Update user balance with atomic operation
        
        Args:
            user: User instance
            amount: Amount to add (positive) or subtract (negative)
            
        Returns:
            Tuple[bool, Dict]: (success, data)
        """
        if not user:
            return False, {"message": "User not found"}
            
        try:
            if amount < 0:
                result = User.objects.filter(pk=user.pk).update(
                    balance=F('balance') + amount
                )
            else:
                result = User.objects.filter(pk=user.pk).update(
                    balance=F('balance') + amount
                )
                
            if result != 1:
                logger.error(f"Failed to update balance for user {user.username}")
                return False, {"message": "Failed to update balance"}
                
            user.refresh_from_db()
            
            log_action = "increased" if amount > 0 else "decreased"
            logger.info(f"Balance {log_action} for user {user.username}: {abs(amount)} = {user.balance}")
            
            return True, {
                "new_balance": user.balance,
                "amount": amount
            }
            
        except Exception as e:
            logger.exception(f"Error updating balance for user {user.username}")
            return False, {"message": "An error occurred while updating balance"}

    @classmethod
    def can_afford(cls, user: User, amount: Decimal) -> Tuple[bool, str]:
        """
        Check if user can afford a payment
        
        Args:
            user: User instance
            amount: Amount to check
            
        Returns:
            Tuple[bool, str]: (can_afford, message)
        """
        if not user:
            return False, "User not found"
            
        available = user.balance + user.overdraft
        
        if available >= amount:
            return True, ""
        else:
            needed = amount - available
            return False, f"Insufficient funds. You need {needed} more to make this payment."

    @classmethod
    @transaction.atomic
    def process_payment(cls, user: User, amount: Decimal, description: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a payment for a user
        
        Args:
            user: User instance
            amount: Amount to pay
            description: Payment description
            
        Returns:
            Tuple[bool, Dict]: (success, data)
        """
        if not user:
            return False, {"message": "User not found"}
            
        can_afford, message = cls.can_afford(user, amount)
        if not can_afford:
            return False, {"message": message}
            
        success, data = cls.update_balance(user, -amount)
        if success:
            # TODO: Create payment record in the Payment model
            # This will be implemented after refactoring the payments app
            data["description"] = description
            return True, data
        else:
            return False, data 
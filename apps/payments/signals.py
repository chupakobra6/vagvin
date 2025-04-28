import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Payment

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Payment)
def payment_status_changed(sender, instance, created, **kwargs):
    """
    Handle payment status changes
    """
    if not created and instance.status == 'success':
        logger.info(f"Payment {instance.id} ({instance.invoice_id}) marked as successful")
        # You can add additional processing here, like sending notifications
        # or triggering other business logic related to successful payments 
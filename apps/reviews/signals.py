from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.template.loader import render_to_string
import logging
from .models import Review
from apps.accounts.utils import send_email

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Review)
def notify_admin_new_review(sender, instance, created, **kwargs):
    if created:
        try:
            admin_url = f"{settings.SITE_URL}/admin/reviews/review/{instance.id}/change/"
            
            context = {
                'review': instance,
                'admin_url': admin_url
            }
            
            html_content = render_to_string('emails/review_notification.html', context)
            
            subject = "Новый отзыв на сайте Vagvin"
            send_email(
                subject=subject,
                to_email=settings.ADMIN_EMAIL,
                html_content=html_content,
                copy_admin=True
            )
            
            logger.info(f"Review notification email sent for review id {instance.id}")
        except Exception as e:
            logger.exception(f"Failed to send email notification for review")
      
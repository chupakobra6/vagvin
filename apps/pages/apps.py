from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pages'
    verbose_name = 'Страницы'

    def ready(self):
        """
        Initialize the app - try to get the Avito token on startup
        """
        # Avoid running this in manage.py commands
        import sys
        if 'runserver' not in sys.argv and 'uwsgi' not in sys.argv and 'asgi' not in sys.argv:
            return
            
        try:
            # Import here to avoid circular imports
            from .services import get_avito_token
            
            logger.info("Attempting to get initial Avito token...")
            token = get_avito_token()
            
            if token:
                logger.info("Successfully obtained and cached initial Avito token.")
            else:
                logger.warning("Failed to get initial Avito token. API calls may fail until token is retrieved.")
                
        except Exception as e:
            logger.exception(f"Error while getting initial Avito token: {e}")

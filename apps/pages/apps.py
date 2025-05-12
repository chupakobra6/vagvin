import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.pages'
    verbose_name = 'Страницы'

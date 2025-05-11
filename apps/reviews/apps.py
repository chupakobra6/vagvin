from django.apps import AppConfig


class ReviewsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.reviews'
    verbose_name = 'Отзывы'

    def ready(self):
        """Import signals when the app is ready."""
        import apps.reviews.signals

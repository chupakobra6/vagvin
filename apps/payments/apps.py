from django.apps import AppConfig


class PaymentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.payments'
    verbose_name = 'Платежи'

    def ready(self):
        """
        Import signal handlers when the app is ready
        """
        from . import signals

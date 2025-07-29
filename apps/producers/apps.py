from django.apps import AppConfig


class ProducersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.producers"
    verbose_name = "Producers"
    
    def ready(self):
        try:
            import apps.producers.signals  # noqa
        except ImportError:
            pass 
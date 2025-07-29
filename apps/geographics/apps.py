from django.apps import AppConfig


class GeographicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.geographics"
    verbose_name = "Geographics"
    
    def ready(self):
        try:
            import apps.geographics.signals  # noqa
        except ImportError:
            pass 
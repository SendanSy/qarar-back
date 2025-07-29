from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"
    
    def ready(self):
        try:
            import apps.users.signals  # noqa
        except ImportError:
            pass

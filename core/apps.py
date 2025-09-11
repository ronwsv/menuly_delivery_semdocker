from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Core"
    
    def ready(self):
        """Registra os signals quando a aplicação estiver pronta"""
        import core.signals  # noqa

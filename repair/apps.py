from django.apps import AppConfig


class RepairConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'repair'

    def ready(self):
        import repair.signals  # noqa
        from .validators import restrict_pillow_formats
        restrict_pillow_formats()

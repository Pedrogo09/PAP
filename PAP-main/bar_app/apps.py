from django.apps import AppConfig

class BarAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bar_app'

    def ready(self):
        import bar_app.signals

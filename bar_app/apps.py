from django.apps import AppConfig

class BarAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bar_app'

    def ready(self):
        import bar_app.signals
        from django.apps import apps
        
        try:
            axes_app = apps.get_app_config('axes')
            axes_app.verbose_name = 'Segurança (Axes)'
            
            model_translations = {
                'AccessAttempt': ('Tentativa de Acesso', 'Tentativas de Acesso'),
                'AccessLog': ('Registo de Acesso', 'Registos de Acesso'),
                'AccessFailureLog': ('Falha de Acesso', 'Falhas de Acesso')
            }
            
            for model_name, (v_name, v_name_plural) in model_translations.items():
                try:
                    model = axes_app.get_model(model_name)
                    model._meta.verbose_name = v_name
                    model._meta.verbose_name_plural = v_name_plural
                except LookupError:
                    pass
        except LookupError:
            pass

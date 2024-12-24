from django.apps import AppConfig


class IvrModelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ivr_model'
    
    def ready(self):
        import ivr_model.signals

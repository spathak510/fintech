from django.apps import AppConfig


class HvWhatsappApiConfig(AppConfig):
    name = 'hv_whatsapp_api'
    
    def ready(self):
        import hv_whatsapp_api.signals

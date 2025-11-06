from django.apps import AppConfig
import os

class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Notifications'
    path = os.path.dirname(os.path.abspath(__file__))
    
    def ready(self):
        import Notifications.signals
from django.apps import AppConfig
import os

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Accounts'
    path = os.path.dirname(os.path.abspath(__file__))
    
    def ready(self):
        import Accounts.signals
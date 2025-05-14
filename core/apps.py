"""
Core app configuration.
"""
from django.apps import AppConfig


class CoreConfig(AppConfig):
    """
    Configuration for the core app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        """
        Connect signal handlers when the app is ready.
        """
        import core.signals
        import core.cache_signals
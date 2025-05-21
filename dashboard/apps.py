"""
Django app configuration for Dashboard module.
"""

from django.apps import AppConfig


class DashboardConfig(AppConfig):
    """
    Configuration for the Dashboard app.
    
    This app provides dashboard views, charts, and statistics for VivaCRM v2.
    It integrates with other modules to display aggregated data and insights.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'dashboard'
    verbose_name = 'Gösterge Paneli'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        This method:
        1. Imports and registers signal handlers
        2. Performs any other app initialization
        """
        # Import signals
        import dashboard.signals
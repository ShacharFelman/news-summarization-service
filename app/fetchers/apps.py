"""
Configuration for the fetchers app.
"""
from django.apps import AppConfig


class FetchersConfig(AppConfig):
    """Configuration class for the fetchers app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fetchers'
    verbose_name = 'Article Fetchers'

    def ready(self):
        """
        Perform initialization when Django starts.
        This is a good place to set up signal handlers if needed.
        """
        pass 

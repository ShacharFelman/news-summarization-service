from django.apps import AppConfig

class SummarizerConfig(AppConfig):
    """Configuration for the summarizer app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'summarizer'
    verbose_name = 'Article Summarizer'

    def ready(self):
        """Initialize the app when Django starts."""
        pass
# """
# Admin configuration for the fetchers app.
# """
from django.contrib import admin
from .models import FetchLog


@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    """Admin configuration for the FetchLog model."""
    list_display = ('source', 'status', 'started_at', 'completed_at',
                    'articles_fetched', 'articles_saved')
    list_filter = ('status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'completed_at', 'articles_fetched',
                       'articles_saved')

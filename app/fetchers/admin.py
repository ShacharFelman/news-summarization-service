# """
# Admin configuration for the fetchers app.
# """
from django.contrib import admin
from .models import FetchLog
# from .models import NewsClientFetcher


# @admin.register(NewsClientFetcher)
# class NewsClientFetcherAdmin(admin.ModelAdmin):
#     """Admin configuration for the NewsClientFetcher model."""
#     list_display = ('name', 'is_active', 'fetch_interval', 'last_fetch')
#     search_fields = ('name',)
#     list_filter = ('is_active',)
#     readonly_fields = ('last_fetch', 'created_at', 'updated_at')


@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    """Admin configuration for the FetchLog model."""
    list_display = ('source', 'status', 'started_at', 'completed_at',
                    'articles_fetched', 'articles_saved')
    list_filter = ('status', 'started_at')
    search_fields = ('error_message',)
    readonly_fields = ('started_at', 'completed_at', 'articles_fetched',
                       'articles_saved')

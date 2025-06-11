# """
# Admin configuration for the fetchers app.
# """
# from django.contrib import admin
# from .models import FetchLog


# @admin.register(FetchLog)
# class FetchLogAdmin(admin.ModelAdmin):
#     """Admin configuration for the FetchLog model."""
#     list_display = ('fetch_type', 'status', 'started_at', 'completed_at',
#                    'articles_fetched', 'articles_saved')
#     list_filter = ('fetch_type', 'status', 'started_at')
#     search_fields = ('error_message',)
#     readonly_fields = ('started_at', 'completed_at', 'articles_fetched',
#                       'articles_saved', 'total_results')
#     fieldsets = (
#         ('Basic Info', {
#             'fields': ('fetch_type', 'status')
#         }),
#         ('Results', {
#             'fields': ('total_results', 'articles_fetched', 'articles_saved')
#         }),
#         ('Timing', {
#             'fields': ('started_at', 'completed_at')
#         }),
#         ('Query Details', {
#             'fields': ('query_params',)
#         }),
#         ('Errors', {
#             'fields': ('error_message',),
#             'classes': ('collapse',)
#         }),
#     )

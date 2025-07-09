from django.contrib import admin
from .models import Summary

@admin.register(Summary)
class SummaryAdmin(admin.ModelAdmin):
    """Admin interface for Summary model."""

    list_display = [
        'article_title_short',
        'ai_model',
        'status',
        'word_count',
        'tokens_used',
        'created_at',
        'completed_at'
    ]

    list_filter = [
        'ai_model',
        'status',
        'created_at',
        'completed_at'
    ]

    search_fields = [
        'article__title',
        'article__source',
        'summary_text'
    ]

    readonly_fields = [
        'created_at',
        'completed_at',
        'tokens_used'
    ]

    fieldsets = (
        ('Article Information', {
            'fields': ('article', 'ai_model', 'requested_by')
        }),
        ('Summary', {
            'fields': ('summary_text', 'word_count', 'status')
        }),
        ('Metadata', {
            'fields': ('tokens_used', 'created_at', 'completed_at')
        }),
        ('Error Information', {
            'fields': ('error_message',),
            'classes': ('collapse',)
        })
    )

    ordering = ['-created_at']

    def article_title_short(self, obj):
        """Display shortened article title."""
        return obj.article.title[:50] + "..." if len(obj.article.title) > 50 else obj.article.title
    article_title_short.short_description = "Article Title"

    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('article', 'requested_by')

    actions = ['mark_as_pending', 'mark_as_failed']

    def mark_as_pending(self, request, queryset):
        """Mark selected summaries as pending."""
        updated = queryset.update(status='pending', error_message=None)
        self.message_user(request, f'{updated} summaries marked as pending.')
    mark_as_pending.short_description = "Mark selected summaries as pending"

    def mark_as_failed(self, request, queryset):
        """Mark selected summaries as failed."""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} summaries marked as failed.')
    mark_as_failed.short_description = "Mark selected summaries as failed"
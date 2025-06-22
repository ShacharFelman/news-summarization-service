"""Models for the fetchers app."""
from django.db import models
from django.utils import timezone


class NewsSource(models.Model):
    """Model representing a news source configuration."""

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Name of the news source"
    )
    source_type = models.CharField(
        max_length=50,
        default='newsapi',
        help_text="Type of the news source (e.g., 'newsapi', 'rss')"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this source is active"
    )
    config = models.JSONField(
        help_text="Source-specific configuration (API keys, URLs, etc.)"
    )
    fetch_interval = models.IntegerField(
        default=6,
        help_text="Hours between fetch operations"
    )
    last_fetch = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the last fetch was performed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = "News Source"
        verbose_name_plural = "News Sources"

    def __str__(self):
        return f"{self.name} ({'active' if self.is_active else 'inactive'})"

    def should_fetch(self) -> bool:
        """Check if it's time to fetch from this source again."""
        if not self.is_active:
            return False

        if not self.last_fetch:
            return True

        hours_since_last_fetch = (
            timezone.now() - self.last_fetch
        ).total_seconds() / 3600
        return hours_since_last_fetch >= self.fetch_interval


class FetchLog(models.Model):
    """Log of article fetch operations."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUCCESS = 'SUCCESS', 'Success'
        ERROR = 'ERROR', 'Error'

    source = models.ForeignKey(
        NewsSource,
        on_delete=models.CASCADE,
        related_name='fetch_logs',
        help_text="The news source used for this fetch"
    )
    fetch_type = models.CharField(
        max_length=20,
        default='everything',
        help_text="Type of fetch operation (e.g., 'everything', 'top-headlines')"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        help_text="Current status of the fetch operation"
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the fetch operation started"
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the fetch operation completed"
    )
    articles_fetched = models.IntegerField(
        default=0,
        help_text="Number of articles fetched from the source"
    )
    articles_saved = models.IntegerField(
        default=0,
        help_text="Number of articles successfully saved"
    )
    error_message = models.TextField(
        blank=True,
        help_text="Error message if the fetch operation failed"
    )
    query_params = models.JSONField(
        default=dict,
        help_text="Parameters used for the fetch operation"
    )
    metadata = models.JSONField(
        default=dict,
        help_text="Additional metadata about the fetch operation"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['fetch_type', '-started_at'])
        ]
        verbose_name = "Fetch Log"
        verbose_name_plural = "Fetch Logs"

    def __str__(self):
        return f"{self.source.name} - {self.status} - {self.started_at}"

    def complete(self, status: Status, **kwargs):
        """Mark the fetch operation as complete with additional data."""
        self.status = status
        self.completed_at = timezone.now()

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.save()
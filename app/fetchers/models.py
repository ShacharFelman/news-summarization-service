"""Models for the fetchers app."""
from django.db import models
from django.utils import timezone
from django.utils.module_loading import import_string


class FetchLog(models.Model):
    """Log of article fetch operations."""

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUCCESS = 'SUCCESS', 'Success'
        ERROR = 'ERROR', 'Error'

    source = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The api source used for this fetch"
    )
    # source = models.ForeignKey(
    #     NewsClientFetcher,
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=True,
    #     related_name='fetch_logs',
    #     help_text="The news source used for this fetch"
    # )
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
    raw_data_file = models.CharField(
        max_length=255,
        blank=True,
        help_text="Path to the raw JSON data file"
    )

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['status', '-started_at']),
        ]
        verbose_name = "Fetch Log"
        verbose_name_plural = "Fetch Logs"

    def __str__(self):
        return f"{self.source if self.source else 'Unknown'} - {self.status} - {self.started_at}"

    def complete(self, status: Status, **kwargs):
        """Mark the fetch operation as complete with additional data."""
        self.status = status
        self.completed_at = timezone.now()

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.save()
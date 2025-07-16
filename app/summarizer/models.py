from django.db import models
from django.conf import settings
from articles.models import Article


class Summary(models.Model):
    """Model to store AI-generated article summaries."""

    SUMMARY_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='summaries',
        help_text="The article being summarized"
    )

    summary_text = models.TextField(
        blank=True,
        null=True,
        help_text="The AI-generated summary text"
    )

    ai_model = models.CharField(
        max_length=50,
        default='openai-gpt-4.1-nano',
        help_text="The AI model used for summarization"
    )

    status = models.CharField(
        max_length=20,
        choices=SUMMARY_STATUS_CHOICES,
        default='pending',
        help_text="Current status of the summarization"
    )

    word_count = models.IntegerField(
        blank=True,
        null=True,
        help_text="Number of words in the summary"
    )

    tokens_used = models.IntegerField(
        blank=True,
        null=True,
        help_text="Number of tokens used by the AI model"
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if summarization failed"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the summary request was created"
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="When the summary was completed"
    )

    # Optional: Track who requested the summary
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="User who requested the summary"
    )

    def __str__(self):
        return f"Summary for: {self.article.title[:50]}..."

    @property
    def is_completed(self):
        return self.status == 'completed'

    @property
    def is_failed(self):
        return self.status == 'failed'

    @property
    def is_pending(self):
        return self.status == 'pending'

    @property
    def is_in_progress(self):
        return self.status == 'in_progress'

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Summary"
        verbose_name_plural = "Summaries"
        # Prevent duplicate summaries for the same article and model
        unique_together = ['article', 'ai_model']
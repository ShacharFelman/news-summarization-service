# """Models for the fetchers app."""
# from django.db import models
# from django.utils import timezone


# class FetchLog(models.Model):
#     """Log of article fetch operations from NewsAPI.org."""

#     FETCH_TYPES = [
#         ('everything', 'Everything'),
#         ('top-headlines', 'Top Headlines'),
#     ]

#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('in_progress', 'In Progress'),
#         ('completed', 'Completed'),
#         ('failed', 'Failed'),
#     ]

#     fetch_type = models.CharField(
#         max_length=20,
#         choices=FETCH_TYPES,
#         help_text="The type of API endpoint used for fetching"
#     )
#     query_params = models.JSONField(
#         default=dict,
#         help_text="The parameters used for the fetch operation"
#     )
#     status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default='pending',
#         help_text="Current status of the fetch operation"
#     )
#     started_at = models.DateTimeField(
#         default=timezone.now,
#         help_text="When the fetch operation started"
#     )
#     completed_at = models.DateTimeField(
#         null=True,
#         blank=True,
#         help_text="When the fetch operation completed"
#     )
#     error_message = models.TextField(
#         blank=True,
#         help_text="Error message if the fetch operation failed"
#     )
#     total_results = models.IntegerField(
#         default=0,
#         help_text="Total number of articles available from the API"
#     )
#     articles_fetched = models.IntegerField(
#         default=0,
#         help_text="Number of articles actually fetched"
#     )
#     articles_saved = models.IntegerField(
#         default=0,
#         help_text="Number of articles successfully saved to database"
#     )

#     class Meta:
#         ordering = ['-started_at']
#         indexes = [
#             models.Index(fields=['status', '-started_at']),
#             models.Index(fields=['fetch_type', '-started_at'])
#         ]
#         verbose_name = "Fetch Log"
#         verbose_name_plural = "Fetch Logs"

#     def __str__(self):
#         return f"{self.fetch_type} - {self.started_at.strftime('%Y-%m-%d %H:%M:%S')} - {self.status}"
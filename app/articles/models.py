from django.utils import timezone
from django.db import models

class Article(models.Model):
    """ Article model representing a news article. """
    title = models.CharField(max_length=255, help_text="The title of the article.")
    content = models.TextField(help_text="The full content of the article.")
    url = models.URLField(unique=True, help_text="The original URL of the article.")
    published_date = models.DateTimeField(help_text="The date and time when the article was published.")
    author = models.CharField(max_length=100, blank=True, null=True, help_text="The author of the article.")
    source = models.CharField(max_length=100, help_text="The source of the article.")
    image_url = models.URLField(blank=True, null=True, help_text="An optional image URL for the article.")
    description = models.TextField(blank=True, null=True, help_text="A brief description or summary of the article.")
    news_client_source = models.CharField(max_length=100, help_text="The news client source of the article.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="The date and time when the article was created.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

from django.db import models

class Article(models.Model):
    title = models.CharField(max_length=255, help_text="The title of the article.")
    content = models.TextField(help_text="The full content of the article.")
    url = models.URLField(unique=True, help_text="The original URL of the article.")
    published_date = models.DateTimeField(help_text="The date and time when the article was published.")
    source = models.CharField(max_length=100, help_text="The source of the article.")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_date']
        verbose_name = "Article"
        verbose_name_plural = "Articles"

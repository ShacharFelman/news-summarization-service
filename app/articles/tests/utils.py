"""
Common test utilities for the articles app.
"""
from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode

from articles.models import Article

def create_article(**params):
    """Create and return an Article instance with default or custom parameters."""
    defaults = {
        'title': 'Sample Article',
        'content': 'Sample content for testing.',
        'url': 'http://example.com/sample',
        'published_date': timezone.now(),
        'source': 'Test Source'
    }
    defaults.update(params)
    return Article.objects.create(**defaults)

def list_url(**query_params):
    """Return URL for the articles list endpoint with optional query parameters."""
    url = reverse('articles:article-list')
    if query_params:
        return f"{url}?{urlencode(query_params)}"
    return url

def detail_url(article_id):
    """Return article detail URL."""
    return reverse('articles:article-detail', args=[article_id])

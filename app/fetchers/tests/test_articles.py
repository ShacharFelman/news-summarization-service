"""Tests for the article fetcher service."""
from django.test import TestCase
from django.utils import timezone
from unittest.mock import patch

from ..services.articles import ArticleFetcher
from ..models import NewsSource
from ..exceptions import ConfigurationError, APIError


class TestArticleFetcher(TestCase):
    """Test suite for ArticleFetcher."""

    def setUp(self):
        """Set up test data."""
        self.source = NewsSource.objects.create(
            name='Test NewsAPI',
            source_type='newsapi',
            config={
                'api_key': 'test_key',
                'base_url': 'https://newsapi.org/v2',
                'category': 'technology'
            }
        )
        self.fetcher = ArticleFetcher(self.source)

    def test_validate_config_missing_api_key(self):
        """Should raise ConfigurationError when API key is missing."""
        self.source.config.pop('api_key')
        self.source.save()

        with self.assertRaises(ConfigurationError):
            self.fetcher.validate_config()

    @patch('httpx.Client')
    def test_fetch_articles_success(self, mock_client):
        """Should fetch and convert articles successfully."""
        # Mock response data
        mock_response = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Test Article',
                    'content': 'Test content',
                    'url': 'http://test.com/article',
                    'publishedAt': '2025-06-12T10:00:00Z',
                    'source': {'name': 'Test Source'}
                }
            ]
        }

        # Set up mock client
        mock_instance = mock_client.return_value.__enter__.return_value
        mock_instance.get.return_value.json.return_value = mock_response

        # Test fetch
        articles = self.fetcher.fetch_articles()

        self.assertEqual(len(articles), 1)
        article = articles[0]
        self.assertEqual(article['title'], 'Test Article')
        self.assertEqual(article['content'], 'Test content')
        self.assertEqual(article['url'], 'http://test.com/article')
        self.assertEqual(article['published_at'], '2025-06-12T10:00:00Z')
        self.assertEqual(article['source_name'], 'Test Source')

"""
Tests for the Article detail view functionalities.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from . import create_article, detail_url

class TestArticleDetailView(TestCase):
    """Test suite for Article detail view functionality."""

    def setUp(self):
        self.client = APIClient()

    def test_retrieve_existing_article(self):
        """Can retrieve an existing article by its ID."""
        article = create_article(
            title='Detail Article',
            url='http://example.com/detail'
        )
        url = detail_url(article.id)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        self.assertEqual(data['id'], article.id)
        self.assertEqual(data['title'], article.title)
        self.assertEqual(data['content'], article.content)
        self.assertEqual(data['url'], article.url)
        self.assertIn('published_date', data)
        self.assertEqual(data['source'], article.source)

    def test_404_for_missing_article(self):
        """Returns 404 when article doesn't exist."""
        url = detail_url(9999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_article_summary(self):
        """Can fetch a summary for an article via the summary endpoint."""
        article = create_article(title='Summary Article', url='http://example.com/summary')
        # Create a completed summary for this article
        from summarizer.models import Summary
        summary = Summary.objects.create(
            article=article,
            summary_text='Short summary.',
            ai_model='gpt-4.1-nano',
            status='completed',
            word_count=2,
            tokens_used=10
        )
        url = detail_url(article.id) + 'summary/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['id'], summary.id)
        self.assertEqual(data['summary_text'], 'Short summary.')
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['ai_model'], 'gpt-4.1-nano')

    def test_get_article_summary_404(self):
        """Returns 404 if no summary exists for the article."""
        article = create_article(title='No Summary', url='http://example.com/nosummary')
        url = detail_url(article.id) + 'summary/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

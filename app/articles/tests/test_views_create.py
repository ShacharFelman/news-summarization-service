"""
Tests for Article creation endpoint functionality.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import datetime

from articles.models import Article
from . import list_url as create_url

class TestArticleCreateView(TestCase):
    """Test suite for article creation endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "title": "Breaking News",
            "content": "Full text of the article.",
            "url": "http://unique.com/1",
            "published_date": (timezone.now() - datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
            "source": "News API"
        }

    def test_create_valid_article_success(self):
        """Valid article data creates new article and returns 201."""
        url = create_url()
        response = self.client.post(url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertEqual(response.data['title'], self.valid_payload['title'])
        self.assertEqual(response.data['content'], self.valid_payload['content'])
        self.assertEqual(response.data['url'], self.valid_payload['url'])
        self.assertEqual(response.data['published_date'], self.valid_payload['published_date'])
        self.assertEqual(response.data['source'], self.valid_payload['source'])

        # Verify in database
        created = Article.objects.get(id=response.data['id'])
        self.assertEqual(created.url, self.valid_payload['url'])

    def test_create_missing_required_field_fails(self):
        """Article creation fails with 400 when required fields are missing."""
        required_fields = ['title', 'content', 'url', 'published_date', 'source']
        url = create_url()

        for field in required_fields:
            invalid_payload = self.valid_payload.copy()
            del invalid_payload[field]

            response = self.client.post(url, invalid_payload, format='json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn(field, response.data)

    def test_create_invalid_url_fails(self):
        """Article creation fails with 400 when URL is invalid."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['url'] = 'not-a-url'

        url = create_url()
        response = self.client.post(url, invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)

    def test_create_duplicate_url_fails(self):
        """Article creation fails with 400 when URL already exists."""
        url = create_url()
        # Create first article
        self.client.post(url, self.valid_payload, format='json')

        # Try to create second article with same URL
        response = self.client.post(url, self.valid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)

    def test_create_future_published_date_fails(self):
        """Article creation fails with 400 when published_date is in future."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['published_date'] = (
            timezone.now() + datetime.timedelta(days=1)
        ).isoformat().replace('+00:00', 'Z')

        url = create_url()
        response = self.client.post(url, invalid_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('published_date', response.data)

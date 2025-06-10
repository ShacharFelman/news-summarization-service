"""
DEPRECATED: This file has been split into separate test files for better organization:
- test_views_list.py: List view tests
- test_views_detail.py: Detail view tests
- test_views_create.py: Creation view tests
- test_integration.py: End-to-end tests
- utils.py: Common test utilities

Please use the new test files instead.
"""

import logging
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
import datetime

from rest_framework import status
from rest_framework.test import APIClient
from urllib.parse import urlencode

from articles.models import Article

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def list_url(**query_params):
    """Return URL for the articles list endpoint with optional query parameters."""
    url = reverse('articles:article-list')
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    return url

def detail_url(article_id):
    """Return article detail URL"""
    return reverse('articles:article-detail', args=[article_id])

def create_article(**params):
    """Helper to create and return an Article instance."""
    defaults = {
        'title': 'Sample Article',
        'content': 'Sample content for testing.',
        'url': 'http://example.com/sample',
        'published_date': timezone.now(),
        'source': 'Test Source'
    }
    defaults.update(params)
    return Article.objects.create(**defaults)

class TestArticleEndpointsNoAuth(TestCase):
    """Test suite for Article API endpoints (no auth, no summary endpoint)."""

    def setUp(self):
        self.client = APIClient()

    #===============================
    # 1. GET /articles/ (Paginated list)
    #===============================

    def test_list_articles_returns_paginated(self):
        """List endpoint returns paginated results for anyone."""
        for i in range(12):
            create_article(
                title=f'Article {i}',
                url=f'http://example.com/{i}',
                published_date=timezone.now() - datetime.timedelta(days=i)
            )
        url = list_url(page=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        self.assertEqual(data['count'], 12)
        self.assertEqual(len(data['results']), 10)
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])
        # Test second page
        next_url = data['next']
        response_page2 = self.client.get(next_url)
        self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
        data2 = response_page2.json()
        self.assertEqual(len(data2['results']), 2)
        self.assertIsNone(data2['next'])
        self.assertIsNotNone(data2['previous'])

    def test_list_articles_page_out_of_range_returns_404(self):
        for i in range(3):
            create_article(title=f'Article {i}', url=f'http://example.com/out/{i}')
        url = list_url(page=9999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    #===============================
    # 2. GET /articles/<id>/ (Detail view)
    #===============================

    def test_retrieve_article_returns_200(self):
        article = create_article(title='Detail Article', url='http://example.com/detail')
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

    def test_retrieve_article_not_found_returns_404(self):
        url = detail_url(9999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    #===============================
    # 3. POST /articles/ (Create view)
    #===============================

    def test_create_article_valid_returns_201(self):
        payload = {
            "title": "Breaking News",
            "content": "Full text of the article.",
            "url": "http://unique.com/1",
            "published_date": (timezone.now() - datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
            "source": "News API"
        }
        url = list_url()
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['title'], payload['title'])
        self.assertEqual(data['content'], payload['content'])
        self.assertEqual(data['url'], payload['url'])
        self.assertEqual(data['published_date'], payload['published_date'])
        self.assertEqual(data['source'], payload['source'])
        # Verify in DB
        created = Article.objects.get(id=data['id'])
        self.assertEqual(created.url, payload['url'])

    def test_create_article_missing_field_returns_400(self):
        payload = {
            # "title" omitted
            "content": "Missing title field.",
            "url": "http://unique.com/2",
            "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
            "source": "News API"
        }
        url = list_url()
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('title', data)
        self.assertEqual(data['title'], ["This field is required."])

    def test_create_article_invalid_url_returns_400(self):
        payload = {
            "title": "Invalid URL Example",
            "content": "Content here.",
            "url": "not-a-valid-url",
            "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
            "source": "News API"
        }
        url = list_url()
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('url', data)

    def test_create_article_duplicate_url_returns_400(self):
        create_article(
            title="Original",
            url="http://duplicate.com/1",
            published_date=timezone.now() - datetime.timedelta(days=1)
        )
        payload = {
            "title": "Duplicate Attempt",
            "content": "Trying to reuse URL.",
            "url": "http://duplicate.com/1",
            "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
            "source": "News API"
        }
        url = list_url()
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('url', data)

    def test_create_article_future_published_date_returns_400(self):
        future_time = (timezone.now() + datetime.timedelta(days=30)).isoformat().replace('+00:00', 'Z')
        payload = {
            "title": "Future Article",
            "content": "This date is in the future.",
            "url": "http://unique.com/3",
            "published_date": future_time,
            "source": "News API"
        }
        url = list_url()
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.json()
        self.assertIn('published_date', data)

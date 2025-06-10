"""
Integration tests for Articles functionality.
Tests that cover multiple layers of the application working together.
"""
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
import datetime

from articles.models import Article
from . import list_url, detail_url

class TestArticlesEndToEnd(TestCase):
    """End-to-end test suite for Articles functionality."""

    def setUp(self):
        self.client = APIClient()
        self.article_data = {
            "title": "Integration Test Article",
            "content": "Content for integration testing.",
            "url": "http://example.com/integration-test",
            "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
            "source": "Integration Tests"
        }

    def test_create_list_retrieve_cycle(self):
        """Test full cycle of creating, listing, and retrieving an article."""
        # Create article
        create_response = self.client.post(
            list_url(),
            self.article_data,
            format='json'
        )
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        created_id = create_response.data['id']

        # Verify it appears in list
        list_response = self.client.get(list_url())
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)
        list_item = list_response.data['results'][0]
        self.assertEqual(list_item['id'], created_id)
        self.assertEqual(list_item['title'], self.article_data['title'])

        # Retrieve and verify details
        detail_response = self.client.get(detail_url(created_id))
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data['id'], created_id)
        self.assertEqual(detail_response.data['title'], self.article_data['title'])
        self.assertEqual(detail_response.data['content'], self.article_data['content'])
        self.assertEqual(detail_response.data['url'], self.article_data['url'])
        self.assertEqual(detail_response.data['source'], self.article_data['source'])

    def test_list_pagination_consistency(self):
        """Test pagination behavior with multiple articles."""
        # Create 15 articles
        for i in range(15):
            article_data = self.article_data.copy()
            article_data['title'] = f"Article {i}"
            article_data['url'] = f"http://example.com/article-{i}"
            response = self.client.post(list_url(), article_data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get first page
        page1_response = self.client.get(list_url())
        self.assertEqual(page1_response.status_code, status.HTTP_200_OK)
        self.assertEqual(page1_response.data['count'], 15)
        self.assertEqual(len(page1_response.data['results']), 10)
        self.assertIsNotNone(page1_response.data['next'])
        self.assertIsNone(page1_response.data['previous'])

        # Get second page
        page2_response = self.client.get(page1_response.data['next'])
        self.assertEqual(page2_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(page2_response.data['results']), 5)
        self.assertIsNone(page2_response.data['next'])
        self.assertIsNotNone(page2_response.data['previous'])

    def test_url_uniqueness_end_to_end(self):
        """Test URL uniqueness constraint through API layer."""
        # Create first article
        response1 = self.client.post(list_url(), self.article_data, format='json')
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)

        # Try to create second article with same URL
        response2 = self.client.post(list_url(), self.article_data, format='json')
        self.assertEqual(response2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response2.data)

        # Verify only one article exists
        list_response = self.client.get(list_url())
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data['count'], 1)
"""
Tests for the Article list view functionalities.
"""
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from . import create_article, list_url

class TestArticleListView(TestCase):
    """Test suite for Article list view functionality."""

    def setUp(self):
        self.client = APIClient()

    def test_returns_paginated_results_success(self):
        """List endpoint returns paginated results."""
        for i in range(12):
            create_article(
                title=f'Article {i}',
                url=f'http://example.com/article-{i}'
            )

        url = list_url(page=1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()

        # Verify pagination structure
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)

        # Verify pagination data
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

    def test_page_out_of_range_handled(self):
        """Returns 404 when requested page is out of range."""
        for i in range(3):
            create_article(
                title=f'Article {i}',
                url=f'http://example.com/article-{i}'
            )

        url = list_url(page=9999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

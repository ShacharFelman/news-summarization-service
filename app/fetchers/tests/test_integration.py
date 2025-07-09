from django.test import TestCase
from unittest.mock import patch, MagicMock
from fetchers.service import NewsApiFetcher
from fetchers.models import FetchLog
from fetchers.exceptions import FetcherError
import os
import logging


class NewsApiFetcherIntegrationTest(TestCase):
    def setUp(self):
        # Suppress fetchers logging during tests
        logging.getLogger('fetchers').setLevel(logging.CRITICAL)
        
        # Store original API key
        self.original_api_key = os.environ.get('NEWSAPI_API_KEY')
        # Set a test API key
        os.environ['NEWSAPI_API_KEY'] = 'test_api_key'

    def tearDown(self):
        # Restore original API key
        if self.original_api_key:
            os.environ['NEWSAPI_API_KEY'] = self.original_api_key
        else:
            os.environ.pop('NEWSAPI_API_KEY', None)

    @patch('httpx.get')
    @patch('articles.models.Article.objects')
    def test_fetch_and_save_success(self, mock_article_manager, mock_get):
        """Test complete fetch_and_save workflow with success."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {
                    'title': 'Test Article 1',
                    'url': 'http://example.com/1',
                    'content': 'Content 1',
                    'publishedAt': '2023-01-01T00:00:00Z',
                    'author': 'Author 1',
                    'source': {'name': 'Test Source'},
                    'urlToImage': 'http://example.com/image1.jpg',
                    'description': 'Description 1'
                },
                {
                    'title': 'Test Article 2',
                    'url': 'http://example.com/2',
                    'content': 'Content 2',
                    'publishedAt': '2023-01-01T01:00:00Z',
                    'author': 'Author 2',
                    'source': {'name': 'Test Source'},
                    'urlToImage': 'http://example.com/image2.jpg',
                    'description': 'Description 2'
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock article manager
        mock_article_manager.filter.return_value.exists.return_value = False

        # Execute fetch_and_save
        fetcher = NewsApiFetcher()
        result = fetcher.fetch_and_save(
            query_params={'category': 'technology'},
            source='TestSource'
        )

        # Verify results
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['totalResults'], 2)
        self.assertEqual(len(result['articles']), 2)
        self.assertEqual(result['articles_processed'], 2)
        self.assertEqual(result['articles_saved'], 2)
        self.assertEqual(result['duplicates_skipped'], 0)

        # Verify fetch log was created
        fetch_logs = FetchLog.objects.all()
        self.assertEqual(len(fetch_logs), 1)
        fetch_log = fetch_logs[0]
        self.assertEqual(fetch_log.source, 'TestSource')
        self.assertEqual(fetch_log.status, FetchLog.Status.SUCCESS)
        self.assertEqual(fetch_log.articles_fetched, 2)
        self.assertEqual(fetch_log.articles_saved, 2)
        # The service adds apiKey to query_params, so we should expect it
        expected_query_params = {'category': 'technology', 'apiKey': 'test_api_key'}
        self.assertEqual(fetch_log.query_params, expected_query_params)

    @patch('httpx.get')
    def test_fetch_and_save_api_error(self, mock_get):
        """Test fetch_and_save with API error."""
        # Mock API error
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception('HTTP 401')
        mock_get.return_value = mock_response

        # Execute fetch_and_save
        fetcher = NewsApiFetcher()
        with self.assertRaises(FetcherError):
            fetcher.fetch_and_save(
                query_params={'category': 'technology'},
                source='TestSource'
            )

        # Verify fetch log was created and marked as error
        fetch_logs = FetchLog.objects.all()
        self.assertEqual(len(fetch_logs), 1)
        fetch_log = fetch_logs[0]
        self.assertEqual(fetch_log.source, 'TestSource')
        self.assertEqual(fetch_log.status, FetchLog.Status.ERROR)
        self.assertIn('Failed to fetch from NewsAPI', fetch_log.error_message)

    @patch('httpx.get')
    @patch('articles.models.Article.objects')
    def test_fetch_and_save_with_duplicates(self, mock_article_manager, mock_get):
        """Test fetch_and_save with duplicate articles."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {
                    'title': 'Test Article 1',
                    'url': 'http://example.com/1',
                    'content': 'Content 1',
                    'publishedAt': '2023-01-01T00:00:00Z',
                    'author': 'Author 1',
                    'source': {'name': 'Test Source'}
                },
                {
                    'title': 'Test Article 2',
                    'url': 'http://example.com/2',
                    'content': 'Content 2',
                    'publishedAt': '2023-01-01T01:00:00Z',
                    'author': 'Author 2',
                    'source': {'name': 'Test Source'}
                }
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Mock article manager - first article exists, second doesn't
        def filter_side_effect(**kwargs):
            mock_filter = MagicMock()
            if kwargs.get('url') == 'http://example.com/1':
                mock_filter.exists.return_value = True
            else:
                mock_filter.exists.return_value = False
            return mock_filter
        
        mock_article_manager.filter.side_effect = filter_side_effect

        # Execute fetch_and_save
        fetcher = NewsApiFetcher()
        result = fetcher.fetch_and_save(
            query_params={'category': 'technology'},
            source='TestSource'
        )

        # Verify results
        self.assertEqual(result['articles_processed'], 2)
        self.assertEqual(result['articles_saved'], 1)
        self.assertEqual(result['duplicates_skipped'], 1)

        # Verify fetch log
        fetch_log = FetchLog.objects.first()
        self.assertEqual(fetch_log.articles_fetched, 2)
        self.assertEqual(fetch_log.articles_saved, 1)

        # Verify that the filter was called with the correct URLs
        self.assertEqual(mock_article_manager.filter.call_count, 2)
        # Check that filter was called with url='http://example.com/1' and url='http://example.com/2'
        mock_article_manager.filter.assert_any_call(url='http://example.com/1')
        mock_article_manager.filter.assert_any_call(url='http://example.com/2')

    @patch('httpx.get')
    def test_fetch_and_save_invalid_response(self, mock_get):
        """Test fetch_and_save with invalid API response."""
        # Mock invalid response (missing articles key)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2
            # Missing 'articles' key
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Execute fetch_and_save
        fetcher = NewsApiFetcher()
        with self.assertRaises(FetcherError):
            fetcher.fetch_and_save(
                query_params={'category': 'technology'},
                source='TestSource'
            )

        # Verify fetch log was created and marked as error
        fetch_log = FetchLog.objects.first()
        self.assertEqual(fetch_log.status, FetchLog.Status.ERROR)
        self.assertIn('Invalid response format', fetch_log.error_message) 
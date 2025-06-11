"""
Service logic tests for fetchers app.
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from fetchers import services
from fetchers.exceptions import FetcherError

class TestFetchersServices(TestCase):
    @override_settings(NEWSAPI_KEY='dummy', ARTICLES_API_URL='http://testserver/api/articles/')
    @patch('fetchers.services.NEWS_FETCHERS', {'newsapi': MagicMock()})
    def test_service_logic(self):
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_articles.return_value = [
            {'title': 'T1', 'content': 'C1', 'url': 'U1', 'published_date': '2024-01-01', 'source': 'newsapi'}
        ]
        services.NEWS_FETCHERS['newsapi'].return_value = mock_fetcher
        with patch('fetchers.services.requests.post') as mock_post:
            mock_post.return_value.status_code = 201
            mock_post.return_value.raise_for_status = lambda: None
            posted, total = services.fetch_and_store_articles('newsapi', {'q': 'python'})
            self.assertEqual(posted, 1)
            self.assertEqual(total, 1)
            mock_post.assert_called_once()

    @override_settings(NEWSAPI_KEY='dummy', ARTICLES_API_URL='http://testserver/api/articles/')
    @patch('fetchers.services.NEWS_FETCHERS', {'newsapi': MagicMock()})
    def test_edge_cases(self):
        # No articles fetched
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_articles.return_value = []
        services.NEWS_FETCHERS['newsapi'].return_value = mock_fetcher
        posted, total = services.fetch_and_store_articles('newsapi', {'q': 'none'})
        self.assertEqual(posted, 0)
        self.assertEqual(total, 0)

    def test_error_handling(self):
        # Unknown fetcher
        with self.assertRaises(FetcherError):
            services.fetch_and_store_articles('unknown', {})
        # Posting error
        with patch('fetchers.services.NEWS_FETCHERS', {'newsapi': MagicMock()}):
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_articles.return_value = [
                {'title': 'T1', 'content': 'C1', 'url': 'U1', 'published_date': '2024-01-01', 'source': 'newsapi'}
            ]
            services.NEWS_FETCHERS['newsapi'].return_value = mock_fetcher
            with patch('fetchers.services.requests.post') as mock_post:
                mock_post.side_effect = Exception('Post failed')
                posted, total = services.fetch_and_store_articles('newsapi', {'q': 'python'})
                self.assertEqual(posted, 0)
                self.assertEqual(total, 1)

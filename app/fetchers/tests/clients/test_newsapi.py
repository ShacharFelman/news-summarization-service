"""
API client tests for fetchers.clients.newsapi
"""
from django.test import TestCase
from unittest.mock import patch
from fetchers.clients.newsapi import NewsAPIFetcher

class TestNewsApiClient(TestCase):
    @patch('fetchers.clients.newsapi.requests.get')
    def test_newsapi_request(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'articles': [{'title': 'T', 'content': 'C', 'url': 'U', 'publishedAt': '2024-01-01'}]}
        fetcher = NewsAPIFetcher('dummy')
        articles = fetcher.fetch_articles(endpoint='top-headlines', q='python')
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'T')

    @patch('fetchers.clients.newsapi.requests.get')
    def test_newsapi_response_parsing(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'articles': [{'title': 'T', 'content': None, 'description': 'D', 'url': 'U', 'publishedAt': '2024-01-01'}]}
        fetcher = NewsAPIFetcher('dummy')
        articles = fetcher.fetch_articles(endpoint='top-headlines', q='python')
        self.assertEqual(articles[0]['content'], 'D')

    @patch('fetchers.clients.newsapi.requests.get')
    def test_newsapi_error_handling(self, mock_get):
        mock_get.side_effect = Exception('fail')
        fetcher = NewsAPIFetcher('dummy')
        with self.assertRaises(Exception):
            fetcher.fetch_articles(endpoint='top-headlines', q='python')

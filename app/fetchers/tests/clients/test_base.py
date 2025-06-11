"""
API client tests for fetchers.clients.base
"""
from django.test import TestCase

from fetchers.clients.base import BaseNewsFetcher


class DummyFetcher(BaseNewsFetcher):
    def fetch_articles(self, **options):
        return [
            {
                "title": "T",
                "content": "C",
                "url": "U",
                "published_date": "2024-01-01",
                "source": "dummy",
            }
        ]


class TestBaseClient(TestCase):
    def test_client_initialization(self):
        fetcher = DummyFetcher()
        self.assertIsInstance(fetcher, BaseNewsFetcher)

    def test_client_request(self):
        fetcher = DummyFetcher()
        articles = fetcher.fetch_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "T")

    def test_error_handling(self):
        class BrokenFetcher(BaseNewsFetcher):
            def fetch_articles(self, **options):
                raise Exception("fail")

        fetcher = BrokenFetcher()
        with self.assertRaises(Exception):
            fetcher.fetch_articles()

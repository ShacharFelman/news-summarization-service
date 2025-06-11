"""
Exception tests for fetchers app.
"""
from django.test import TestCase
from fetchers.exceptions import FetcherError

class TestFetchersExceptions(TestCase):
    def test_custom_exceptions(self):
        with self.assertRaises(FetcherError):
            raise FetcherError('Test error')

    def test_exception_handling(self):
        try:
            raise FetcherError('Handled error')
        except FetcherError as e:
            self.assertEqual(str(e), 'Handled error')

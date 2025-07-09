from django.test import TestCase
from rest_framework.test import APITestCase
import logging


class BaseTestCase(TestCase):
    """Base test case with logging suppression for clean test output."""
    
    def setUp(self):
        super().setUp()
        # Suppress common loggers during tests
        logging.getLogger('summarizer').setLevel(logging.CRITICAL)
        logging.getLogger('fetchers').setLevel(logging.CRITICAL)
        logging.getLogger('articles').setLevel(logging.CRITICAL)


class BaseAPITestCase(APITestCase):
    """Base API test case with logging suppression for clean test output."""
    
    def setUp(self):
        super().setUp()
        # Suppress common loggers during tests
        logging.getLogger('summarizer').setLevel(logging.CRITICAL)
        logging.getLogger('fetchers').setLevel(logging.CRITICAL)
        logging.getLogger('articles').setLevel(logging.CRITICAL) 
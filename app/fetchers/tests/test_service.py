from django.test import TestCase
from unittest.mock import patch, MagicMock
from fetchers.service import NewsApiFetcher
from fetchers.exceptions import ConfigurationError, FetcherError
from fetchers.models import FetchLog
import os


class NewsApiFetcherTest(TestCase):
    def setUp(self):
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

    def test_initialization_with_env_api_key(self):
        """Test initialization with API key from environment."""
        fetcher = NewsApiFetcher()
        self.assertEqual(fetcher.api_key, 'test_api_key')
        self.assertEqual(fetcher.base_url, 'https://newsapi.org/v2/top-headlines')

    def test_initialization_with_config_api_key(self):
        """Test initialization with API key from config."""
        config = {'api_key': 'config_api_key'}
        fetcher = NewsApiFetcher(config=config)
        self.assertEqual(fetcher.api_key, 'config_api_key')

    def test_initialization_without_api_key(self):
        """Test initialization fails without API key."""
        os.environ.pop('NEWSAPI_API_KEY', None)
        with self.assertRaises(ConfigurationError):
            NewsApiFetcher()

    def test_get_query_params_default(self):
        """Test default query parameters."""
        fetcher = NewsApiFetcher()
        params = fetcher._get_query_params()
        self.assertEqual(params['language'], 'en')
        self.assertEqual(params['category'], 'technology')

    def test_get_query_params_with_config(self):
        """Test query parameters with custom config."""
        config = {
            'language': 'es',
            'category': 'business',
            'country': 'us'
        }
        fetcher = NewsApiFetcher(config=config)
        params = fetcher._get_query_params()
        self.assertEqual(params['language'], 'es')
        self.assertEqual(params['category'], 'business')
        self.assertEqual(params['country'], 'us')
        self.assertNotIn('api_key', params)  # api_key should be excluded

    def test_create_fetch_log(self):
        """Test fetch log creation."""
        fetcher = NewsApiFetcher()
        query_params = {'category': 'technology'}
        
        fetch_log = fetcher._create_fetch_log('TestSource', query_params)
        
        self.assertEqual(fetch_log.source, 'TestSource')
        self.assertEqual(fetch_log.status, FetchLog.Status.PENDING)
        self.assertEqual(fetch_log.query_params, query_params)
        self.assertEqual(fetch_log.metadata['fetcher_class'], 'NewsApiFetcher')

    @patch('httpx.get')
    def test_fetch_articles_success(self, mock_get):
        """Test successful API call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [
                {'title': 'Article 1', 'url': 'http://example.com/1'},
                {'title': 'Article 2', 'url': 'http://example.com/2'}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher = NewsApiFetcher()
        result = fetcher._fetch_articles({'category': 'technology'})

        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['totalResults'], 2)
        self.assertEqual(len(result['articles']), 2)

    @patch('httpx.get')
    def test_fetch_articles_api_error(self, mock_get):
        """Test API call with error response."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception('HTTP 401')
        mock_get.return_value = mock_response

        fetcher = NewsApiFetcher()
        with self.assertRaises(FetcherError):
            fetcher._fetch_articles({'category': 'technology'})

    def test_process_response_valid(self):
        """Test processing valid response."""
        fetcher = NewsApiFetcher()
        response_data = {
            'status': 'ok',
            'totalResults': 2,
            'articles': [{'title': 'Test'}]
        }
        
        result = fetcher._process_response(response_data)
        
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['totalResults'], 2)
        self.assertEqual(len(result['articles']), 1)

    def test_process_response_invalid(self):
        """Test processing invalid response."""
        fetcher = NewsApiFetcher()
        response_data = {'status': 'ok'}  # Missing 'articles' key
        
        with self.assertRaises(FetcherError):
            fetcher._process_response(response_data)

    @patch('articles.models.Article.objects')
    def test_save_articles_success(self, mock_article_manager):
        """Test saving articles successfully."""
        fetcher = NewsApiFetcher()
        articles_data = [
            {
                'title': 'Test Article',
                'url': 'http://example.com/test',
                'content': 'Test content',
                'publishedAt': '2023-01-01T00:00:00Z',
                'author': 'Test Author',
                'source': {'name': 'Test Source'},
                'urlToImage': 'http://example.com/image.jpg',
                'description': 'Test description'
            }
        ]
        
        # Mock that no article exists with this URL
        mock_article_manager.filter.return_value.exists.return_value = False
        
        processed, saved = fetcher._save_articles(articles_data)
        
        self.assertEqual(processed, 1)
        self.assertEqual(saved, 1)
        mock_article_manager.create.assert_called_once()

    @patch('articles.models.Article.objects')
    def test_save_articles_duplicate_skip(self, mock_article_manager):
        """Test skipping duplicate articles."""
        fetcher = NewsApiFetcher()
        articles_data = [
            {
                'title': 'Test Article',
                'url': 'http://example.com/test',
                'content': 'Test content',
                'publishedAt': '2023-01-01T00:00:00Z',
                'author': 'Test Author',
                'source': {'name': 'Test Source'}
            }
        ]
        
        # Mock that article already exists with this URL
        mock_article_manager.filter.return_value.exists.return_value = True
        
        processed, saved = fetcher._save_articles(articles_data)
        
        self.assertEqual(processed, 1)
        self.assertEqual(saved, 0)  # Should skip duplicate
        mock_article_manager.create.assert_not_called() 
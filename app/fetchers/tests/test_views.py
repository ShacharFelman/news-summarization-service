from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework.authtoken.models import Token
from users.models import User
from unittest.mock import patch, MagicMock
from fetchers.models import FetchLog


class ArticleFetchViewTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@example.com', password='adminpass', name='Admin User', is_staff=True)
        self.token = Token.objects.create(user=self.user)
        self.regular_user = User.objects.create_user(email='user@example.com', password='userpass', name='Regular User')
        self.user_token = Token.objects.create(user=self.regular_user)

    def test_fetch_articles_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        url = reverse('fetchers:fetch_articles')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_fetch_articles_authenticated_admin(self):
        """Test successful article fetching with admin authentication (allowed)."""
        with patch('fetchers.views.NewsApiFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('fetchers:fetch_articles')
            data = {'query_params': {'category': 'technology'}}
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, 200)
            self.assertIn('message', response.data)
            mock_fetcher.fetch_and_save.assert_called_once_with(
                {'category': 'technology'}, 
                source='NewsClientFetcher'
            )

    def test_fetch_articles_authenticated_non_admin(self):
        """Test that non-admin authenticated users are forbidden."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('fetchers:fetch_articles')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_fetch_articles_without_query_params(self):
        """Test article fetching without query parameters."""
        with patch('fetchers.views.NewsApiFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher_class.return_value = mock_fetcher
            
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('fetchers:fetch_articles')
            
            response = self.client.post(url, {}, format='json')
            
            self.assertEqual(response.status_code, 200)
            mock_fetcher.fetch_and_save.assert_called_once_with(
                None, 
                source='NewsClientFetcher'
            )

    def test_fetch_articles_fetcher_error(self):
        """Test handling of FetcherError."""
        with patch('fetchers.views.NewsApiFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_and_save.side_effect = Exception('FetcherError: API key invalid')
            mock_fetcher_class.return_value = mock_fetcher
            
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('fetchers:fetch_articles')
            
            response = self.client.post(url, {}, format='json')
            
            self.assertEqual(response.status_code, 500)
            self.assertIn('error', response.data)

    def test_fetch_articles_unexpected_error(self):
        """Test handling of unexpected errors."""
        with patch('fetchers.views.NewsApiFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_and_save.side_effect = Exception('Unexpected error')
            mock_fetcher_class.return_value = mock_fetcher
            
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('fetchers:fetch_articles')
            
            response = self.client.post(url, {}, format='json')
            
            self.assertEqual(response.status_code, 500)
            self.assertIn('error', response.data)
            self.assertIn('Internal server error.', response.data['error'])

    def test_fetch_articles_method_not_allowed(self):
        """Test that GET requests are not allowed."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('fetchers:fetch_articles')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)  # Method Not Allowed 
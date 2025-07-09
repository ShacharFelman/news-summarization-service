from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch, MagicMock
from summarizer.models import Summary
from articles.models import Article
import logging


class SummarizerViewsTest(APITestCase):
    """Test cases for summarizer views."""

    def setUp(self):
        """Set up test data."""
        # Suppress summarizer logging during tests
        logging.getLogger('summarizer').setLevel(logging.CRITICAL)
        
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.token = Token.objects.create(user=self.user)
        
        self.article = Article.objects.create(
            title='Test Article',
            content='This is a test article content for testing purposes.',
            url='http://example.com/test',
            published_date=timezone.now(),
            author='Test Author',
            source='Test Source',
            news_client_source='TestAPI'
        )
        
        self.summary = Summary.objects.create(
            article=self.article,
            summary_text='This is a test summary of the article.',
            ai_model='gpt-4.1-nano',
            status='completed',
            word_count=15,
            tokens_used=75,
            requested_by=self.user,
            completed_at=timezone.now()
        )

    def test_summarize_article_authenticated(self):
        """Test summarize article endpoint with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.summarize_article') as mock_summarize:
            mock_summarize.return_value = self.summary
            
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': self.article.id,
                'ai_model': 'gpt-4.1-nano',
                'max_words': 150
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['summary']['id'], self.summary.id)
            self.assertEqual(response.data['summary']['article_id'], self.article.id)
            self.assertEqual(response.data['summary']['ai_model'], 'gpt-4.1-nano')
            self.assertEqual(response.data['summary']['status'], 'completed')

    def test_summarize_article_unauthenticated(self):
        """Test summarize article endpoint without authentication."""
        url = reverse('summarizer:summarize_article')
        response = self.client.post(url, {
            'article_id': self.article.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summarize_article_missing_article_id(self):
        """Test summarize article with missing article_id."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('summarizer:summarize_article')
        response = self.client.post(url, {
            'ai_model': 'gpt-4.1-nano'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('article_id is required', response.data['error'])

    def test_summarize_article_service_error(self):
        """Test summarize article when service raises an error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.summarize_article') as mock_summarize:
            mock_summarize.side_effect = ValueError('Article not found')
            
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': 999,
                'ai_model': 'gpt-4.1-nano'
            })
            
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn('Article not found', response.data['error'])

    def test_summarize_article_internal_error(self):
        """Test summarize article when service raises internal error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.summarize_article') as mock_summarize:
            mock_summarize.side_effect = Exception('Internal error')
            
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': self.article.id,
                'ai_model': 'gpt-4.1-nano'
            })
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Internal server error', response.data['error'])

    def test_get_summary_authenticated(self):
        """Test get summary endpoint with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = self.summary
            
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['summary']['id'], self.summary.id)
            self.assertEqual(response.data['summary']['article_id'], self.article.id)

    def test_get_summary_unauthenticated(self):
        """Test get summary endpoint without authentication."""
        url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_summary_not_found(self):
        """Test get summary when summary doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = None
            
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn('Summary not found', response.data['error'])

    def test_get_summary_with_ai_model(self):
        """Test get summary with specific AI model."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = self.summary
            
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url, {'ai_model': 'gpt-3.5-turbo'})
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            # Verify the service was called with the correct ai_model
            mock_get.assert_called_with(article_id=self.article.id, ai_model='gpt-3.5-turbo')

    def test_get_all_summaries_authenticated(self):
        """Test get all summaries endpoint with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.get_article_summaries') as mock_get:
            mock_get.return_value = {
                'article_id': self.article.id,
                'summaries': [
                    {
                        'id': self.summary.id,
                        'ai_model': self.summary.ai_model,
                        'status': self.summary.status,
                        'summary_text': self.summary.summary_text
                    }
                ]
            }
            
            url = reverse('summarizer:get_all_summaries', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['data']['article_id'], self.article.id)
            self.assertEqual(len(response.data['data']['summaries']), 1)

    def test_get_all_summaries_unauthenticated(self):
        """Test get all summaries endpoint without authentication."""
        url = reverse('summarizer:get_all_summaries', kwargs={'article_id': self.article.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_summaries_service_error(self):
        """Test get all summaries when service raises an error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        with patch('summarizer.service.SummarizerService.get_article_summaries') as mock_get:
            mock_get.side_effect = Exception('Database error')
            
            url = reverse('summarizer:get_all_summaries', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Internal server error', response.data['error'])

    def test_summary_status_authenticated(self):
        """Test summary status endpoint with authentication."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('summarizer:summary_status', kwargs={'summary_id': self.summary.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status']['id'], self.summary.id)
        self.assertEqual(response.data['status']['status'], 'completed')

    def test_summary_status_unauthenticated(self):
        """Test summary status endpoint without authentication."""
        url = reverse('summarizer:summary_status', kwargs={'summary_id': self.summary.id})
        response = self.client.get(url)
        
        # The summary_status view doesn't require authentication
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['status']['id'], self.summary.id)

    def test_summary_status_not_found(self):
        """Test summary status when summary doesn't exist."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('summarizer:summary_status', kwargs={'summary_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('Summary not found', response.data['error'])

    def test_summary_status_with_error(self):
        """Test summary status with failed summary."""
        failed_summary = Summary.objects.create(
            article=self.article,
            status='failed',
            error_message='API rate limit exceeded',
            ai_model='gpt-3.5-turbo'
        )
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('summarizer:summary_status', kwargs={'summary_id': failed_summary.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status']['status'], 'failed')
        self.assertEqual(response.data['status']['error_message'], 'API rate limit exceeded') 
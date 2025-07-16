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
        self.admin_user = get_user_model().objects.create_user(
            email='admin@example.com',
            name='Admin User',
            password='adminpass',
            is_staff=True
        )
        self.admin_token = Token.objects.create(user=self.admin_user)
        
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

    def test_summarize_article_authenticated_admin(self):
        """Test summarize article endpoint with admin authentication (allowed, async)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        with patch('summarizer.service.SummarizerService.summarize_article_async') as mock_summarize_async:
            # Simulate in_progress summary
            summary_in_progress = self.summary
            summary_in_progress.status = 'in_progress'
            mock_summarize_async.return_value = summary_in_progress
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': self.article.id,
                'ai_model': 'gpt-4.1-nano',
                'max_words': 150
            })
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertTrue(response.data['success'])
            self.assertIn('being processed', response.data['message'].lower())
            # Simulate completed summary
            summary_completed = self.summary
            summary_completed.status = 'completed'
            mock_summarize_async.return_value = summary_completed
            response = self.client.post(url, {
                'article_id': self.article.id,
                'ai_model': 'gpt-4.1-nano',
                'max_words': 150
            })
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])

    def test_summarize_article_authenticated_non_admin(self):
        """Test summarize article endpoint with non-admin authentication (forbidden)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('summarizer:summarize_article')
        response = self.client.post(url, {
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summarize_article_unauthenticated(self):
        """Test summarize article endpoint without authentication."""
        url = reverse('summarizer:summarize_article')
        response = self.client.post(url, {
            'article_id': self.article.id
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summarize_article_missing_article_id(self):
        """Test summarize article with missing article_id."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('summarizer:summarize_article')
        response = self.client.post(url, {
            'ai_model': 'gpt-4.1-nano'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('article_id is required', response.data['error'])

    def test_summarize_article_service_error(self):
        """Test summarize article when service raises an error (article not found)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        with patch('summarizer.service.SummarizerService.summarize_article_async') as mock_summarize_async:
            mock_summarize_async.side_effect = Article.DoesNotExist()
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': 999,
                'ai_model': 'gpt-4.1-nano'
            })
            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
            self.assertIn('Article not found', response.data['error'])

    def test_summarize_article_internal_error(self):
        """Test summarize article when service raises internal error."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        with patch('summarizer.service.SummarizerService.summarize_article_async') as mock_summarize_async:
            mock_summarize_async.side_effect = Exception('Internal error')
            url = reverse('summarizer:summarize_article')
            response = self.client.post(url, {
                'article_id': self.article.id,
                'ai_model': 'gpt-4.1-nano'
            })
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            self.assertIn('Internal server error', response.data['error'])

    def test_get_summary_authenticated_admin(self):
        """Test get summary endpoint with admin authentication (allowed)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = self.summary
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])

    def test_get_summary_authenticated_non_admin(self):
        """Test get summary endpoint with non-admin authentication (forbidden)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = self.summary
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_summary_unauthenticated(self):
        """Test get summary endpoint without authentication."""
        url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_summary_not_found(self):
        """Test get summary when summary doesn't exist (forbidden for non-admin)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = None
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_summary_with_ai_model(self):
        """Test get summary with specific AI model (forbidden for non-admin)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        with patch('summarizer.service.SummarizerService.get_article_summary') as mock_get:
            mock_get.return_value = self.summary
            url = reverse('summarizer:get_summary', kwargs={'article_id': self.article.id})
            response = self.client.get(url, {'ai_model': 'gpt-3.5-turbo'})
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_summaries_authenticated_admin(self):
        """Test get all summaries endpoint with admin authentication (allowed)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
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

    def test_get_all_summaries_authenticated_non_admin(self):
        """Test get all summaries endpoint with non-admin authentication (forbidden)."""
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
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_all_summaries_unauthenticated(self):
        """Test get all summaries endpoint without authentication."""
        url = reverse('summarizer:get_all_summaries', kwargs={'article_id': self.article.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_all_summaries_service_error(self):
        """Test get all summaries when service raises an error (should be forbidden for non-admin)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        with patch('summarizer.service.SummarizerService.get_article_summaries') as mock_get:
            mock_get.side_effect = Exception('Database error')
            url = reverse('summarizer:get_all_summaries', kwargs={'article_id': self.article.id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_status_authenticated(self):
        """Test summary status endpoint with authentication (forbidden for non-admin)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('summarizer:summary_status', kwargs={'summary_id': self.summary.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_status_unauthenticated(self):
        """Test summary status endpoint without authentication."""
        url = reverse('summarizer:summary_status', kwargs={'summary_id': self.summary.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_summary_status_not_found(self):
        """Test summary status when summary doesn't exist (forbidden for non-admin)."""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('summarizer:summary_status', kwargs={'summary_id': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_summary_status_with_error(self):
        """Test summary status with failed summary (forbidden for non-admin)."""
        failed_summary = Summary.objects.create(
            article=self.article,
            status='failed',
            error_message='API rate limit exceeded',
            ai_model='gpt-3.5-turbo'
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('summarizer:summary_status', kwargs={'summary_id': failed_summary.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN) 
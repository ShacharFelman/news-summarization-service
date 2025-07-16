from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, Mock
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User
import logging
from rest_framework import status

class ArticleSummaryIntegrationTest(APITestCase):
    def setUp(self):
        # Suppress summarizer logging during tests
        logging.getLogger('summarizer').setLevel(logging.CRITICAL)
        
        self.user = User.objects.create_user(email='admin@example.com', password='adminpass', name='Admin User', is_staff=True)
        self.token = Token.objects.create(user=self.user)
        self.article = Article.objects.create(
            title="Test Article",
            content="Some content",
            url="http://example.com/article",
            published_date=timezone.now(),
            author="Author Name",
            source="Test Source",
            news_client_source="Test Client"
        )

    @patch('articles.views.SummarizerService')
    def test_summary_action_success(self, mock_summarizer_service_class):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            mock_service_instance = Mock()
            mock_summary = Mock()
            mock_summary.id = 1
            mock_summary.article = self.article
            mock_summary.summary_text = 'Test summary'
            mock_summary.ai_model = 'gpt-4.1-nano'
            mock_summary.word_count = 10
            mock_summary.tokens_used = 50
            mock_summary.created_at = timezone.now()
            mock_summary.completed_at = timezone.now()
            # Simulate in_progress summary
            mock_summary.status = 'in_progress'
            mock_service_instance.summarize_article_async.return_value = mock_summary
            mock_summarizer_service_class.return_value = mock_service_instance
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('articles:articles-summary', args=[self.article.id])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 202)
            self.assertIn('being processed', response.data['message'].lower())
            # Simulate completed summary
            mock_summary.status = 'completed'
            mock_service_instance.summarize_article_async.return_value = mock_summary
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.data['success'])
            mock_service_instance.summarize_article_async.assert_called_with(article_id=str(self.article.id), user=self.user)

    @patch('articles.views.SummarizerService')
    def test_summary_action_article_not_found(self, mock_summarizer_service_class):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            mock_service_instance = Mock()
            mock_service_instance.summarize_article_async.side_effect = Article.DoesNotExist  # Use class, not instance
            mock_summarizer_service_class.return_value = mock_service_instance

            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('articles:articles-summary', args=[9999])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertIn('detail', response.data) 

class ArticleSummaryAsyncTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(email='user@example.com', password='userpass', name='User', is_staff=True)
        cls.token = Token.objects.create(user=cls.user)
        cls.article = Article.objects.create(
            title="Async Test Article",
            content="Async content",
            url="http://example.com/async-article",
            published_date=timezone.now(),
            author="Async Author",
            source="Async Source",
            news_client_source="Async Client"
        )

    def _auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def _summary_url(self, article_id=None):
        return reverse('articles:articles-summary', args=[article_id or self.article.id])

    def _mock_service(self, status=None, side_effect=None):
        mock_service_instance = Mock()
        mock_summary = Mock()
        if status:
            mock_summary.status = status
            mock_service_instance.summarize_article_async.return_value = mock_summary
        if side_effect:
            mock_service_instance.summarize_article_async.side_effect = side_effect
        # Set required attributes for serializer
        mock_summary.id = 1
        mock_summary.article = self.article
        mock_summary.summary_text = 'Test summary' if status == 'completed' else None
        mock_summary.ai_model = 'gpt-4.1-nano'
        mock_summary.word_count = 10
        mock_summary.tokens_used = 50
        mock_summary.created_at = timezone.now()
        mock_summary.completed_at = timezone.now() if status == 'completed' else None
        mock_summary.error_message = None
        return mock_service_instance, mock_summary

    @patch('articles.views.SummarizerService')
    def test_summary_async_returns_202_pending(self, mock_summarizer_service_class):
        mock_service_instance, _ = self._mock_service(status='pending')
        mock_summarizer_service_class.return_value = mock_service_instance
        self._auth()
        url = self._summary_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('being processed', response.data['message'].lower())

    @patch('articles.views.SummarizerService')
    def test_summary_async_returns_202_if_still_pending(self, mock_summarizer_service_class):
        mock_service_instance, _ = self._mock_service(status='in_progress')
        mock_summarizer_service_class.return_value = mock_service_instance
        self._auth()
        url = self._summary_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn('being processed', response.data['message'].lower())

    @patch('articles.views.SummarizerService')
    def test_summary_async_returns_500_if_failed(self, mock_summarizer_service_class):
        mock_service_instance, _ = self._mock_service(status='failed')
        mock_summarizer_service_class.return_value = mock_service_instance
        self._auth()
        url = self._summary_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('failed', response.data['message'].lower())

    @patch('articles.views.SummarizerService')
    def test_summary_async_returns_404_if_article_not_found(self, mock_summarizer_service_class):
        # Directly set side_effect to raise Article.DoesNotExist, do not create a mock summary
        mock_service_instance = Mock()
        mock_service_instance.summarize_article_async.side_effect = Article.DoesNotExist
        mock_summarizer_service_class.return_value = mock_service_instance
        self._auth()
        url = self._summary_url(article_id=99999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['detail'].lower())

    @patch('summarizer.tasks.summarize_article_task.delay')
    @patch('summarizer.models.Summary.objects.get_or_create')
    def test_summary_async_enqueues_celery_task(self, mock_get_or_create, mock_celery_delay):
        # Simulate a new summary being created
        mock_summary = Mock()
        mock_summary.status = 'pending'  # Changed from 'new' to 'pending' to match view expectations
        mock_summary.id = 1
        mock_summary.article = self.article  # Use a real Article instance
        mock_summary.summary_text = 'Test summary'
        mock_summary.ai_model = 'gpt-4.1-nano'
        mock_summary.word_count = 10
        mock_summary.tokens_used = 50
        mock_summary.created_at = timezone.now()
        mock_summary.completed_at = None
        mock_summary.error_message = None
        mock_get_or_create.return_value = (mock_summary, True)
        self._auth()
        url = self._summary_url()
        self.client.get(url)
        self.assertTrue(mock_celery_delay.called) 
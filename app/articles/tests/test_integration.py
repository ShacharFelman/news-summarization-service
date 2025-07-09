from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch, MagicMock
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User
import logging

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
        # Set up environment variable to avoid ValueError in service init
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create a mock instance
            mock_service_instance = MagicMock()
            mock_summary = MagicMock()
            mock_summary.id = 1
            mock_summary.article = self.article
            mock_summary.summary_text = 'Test summary'
            mock_summary.ai_model = 'gpt-4.1-nano'
            mock_summary.status = 'completed'
            mock_summary.word_count = 10
            mock_summary.tokens_used = 50
            mock_summary.created_at = timezone.now()
            mock_summary.completed_at = timezone.now()
            mock_service_instance.summarize_article.return_value = mock_summary
            mock_summarizer_service_class.return_value = mock_service_instance

            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('articles:articles-summary', args=[self.article.id])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            # The view passes pk (string from URL) directly to summarize_article
            mock_service_instance.summarize_article.assert_called_once_with(article_id=str(self.article.id))

    @patch('articles.views.SummarizerService')
    def test_summary_action_article_not_found(self, mock_summarizer_service_class):
        # Set up environment variable to avoid ValueError in service init
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            # Create a mock instance
            mock_service_instance = MagicMock()
            mock_service_instance.summarize_article.side_effect = Article.DoesNotExist
            mock_summarizer_service_class.return_value = mock_service_instance

            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
            url = reverse('articles:articles-summary', args=[9999])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)
            self.assertIn('detail', response.data) 
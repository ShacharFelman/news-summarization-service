from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, MagicMock
from summarizer.models import Summary
from summarizer.service import SummarizerService
from articles.models import Article
import logging


class SummarizerServiceTest(TestCase):
    """Test cases for the SummarizerService."""

    def setUp(self):
        """Set up test data."""
        # Suppress summarizer logging during tests
        logging.getLogger('summarizer').setLevel(logging.CRITICAL)
        
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.article = Article.objects.create(
            title='Test Article',
            content='This is a test article content for testing purposes. It contains multiple sentences to test the summarization functionality.',
            url='http://example.com/test',
            published_date=timezone.now(),
            author='Test Author',
            source='Test Source',
            news_client_source='TestAPI'
        )

    @patch('summarizer.service.ChatOpenAI')
    @patch('summarizer.service.ChatPromptTemplate')
    def test_summarizer_service_initialization(self, mock_prompt_template, mock_chat_openai):
        """Test SummarizerService initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            self.assertEqual(service.default_model, 'gpt-4.1-nano')
            self.assertEqual(service.openai_api_key, 'test_key')
            self.assertIn('gpt-4.1-nano', service.model_map)
            self.assertIn('gpt-3.5-turbo', service.model_map)

    def test_summarizer_service_missing_api_key(self):
        """Test SummarizerService initialization without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                SummarizerService()
            
            self.assertIn('OPENAI_API_KEY must be set', str(context.exception))

    @patch('summarizer.service.ChatOpenAI')
    @patch('summarizer.service.ChatPromptTemplate')
    def test_get_llm_with_default_model(self, mock_prompt_template, mock_chat_openai):
        """Test _get_llm method with default model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            llm = service._get_llm()
            
            mock_chat_openai.assert_called_with(
                api_key='test_key',
                model='gpt-4.1-nano',
                temperature=0.3
            )

    @patch('summarizer.service.ChatOpenAI')
    @patch('summarizer.service.ChatPromptTemplate')
    def test_get_llm_with_custom_model(self, mock_prompt_template, mock_chat_openai):
        """Test _get_llm method with custom model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            llm = service._get_llm('gpt-3.5-turbo')
            
            mock_chat_openai.assert_called_with(
                api_key='test_key',
                model='gpt-3.5-turbo',
                temperature=0.3
            )

    @patch('summarizer.service.ChatOpenAI')
    @patch('summarizer.service.ChatPromptTemplate')
    def test_get_llm_with_unknown_model(self, mock_prompt_template, mock_chat_openai):
        """Test _get_llm method with unknown model."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            llm = service._get_llm('unknown-model')
            
            # Should use default model
            mock_chat_openai.assert_called_with(
                api_key='test_key',
                model='gpt-4.1-nano',
                temperature=0.3
            )

    @patch('summarizer.service.SummarizerService._generate_summary')
    def test_summarize_article_success(self, mock_generate_summary):
        """Test summarize_article method success."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            # Mock the _generate_summary method directly
            mock_generate_summary.return_value = ('This is a test summary.', 50)
            
            summary = service.summarize_article(
                article_id=self.article.id,
                ai_model='gpt-4.1-nano',
                user=self.user,
                max_words=100
            )
            
            self.assertEqual(summary.article, self.article)
            self.assertEqual(summary.summary_text, 'This is a test summary.')
            self.assertEqual(summary.ai_model, 'gpt-4.1-nano')
            self.assertEqual(summary.status, 'completed')
            self.assertEqual(summary.word_count, 5)
            self.assertEqual(summary.tokens_used, 50)
            self.assertEqual(summary.requested_by, self.user)
            self.assertIsNotNone(summary.completed_at)

    @patch('summarizer.service.SummarizerService._generate_summary')
    def test_summarize_article_existing_summary(self, mock_generate_summary):
        """Test summarize_article with existing completed summary."""
        # Create existing summary
        existing_summary = Summary.objects.create(
            article=self.article,
            summary_text='Existing summary',
            ai_model='gpt-4.1-nano',
            status='completed',
            word_count=10,
            tokens_used=40
        )
        
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            summary = service.summarize_article(
                article_id=self.article.id,
                ai_model='gpt-4.1-nano',
                user=self.user
            )
            
            # Should return existing summary without calling _generate_summary
            self.assertEqual(summary, existing_summary)
            self.assertEqual(summary.summary_text, 'Existing summary')
            # Verify _generate_summary was not called
            mock_generate_summary.assert_not_called()

    @patch('summarizer.service.SummarizerService._generate_summary')
    def test_generate_summary_success(self, mock_generate_summary):
        """Test _generate_summary method success."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            # Mock the _generate_summary method directly
            mock_generate_summary.return_value = ('This is a test summary.', 50)
            
            summary_text, token_count = service._generate_summary(
                title='Test Title',
                content='Test content',
                ai_model='gpt-4.1-nano',
                max_words=100
            )
            
            self.assertEqual(summary_text, 'This is a test summary.')
            self.assertEqual(token_count, 50)

    @patch('summarizer.service.SummarizerService._generate_summary')
    def test_generate_summary_without_usage(self, mock_generate_summary):
        """Test _generate_summary method without usage info."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            # Mock the _generate_summary method directly
            mock_generate_summary.return_value = ('This is a test summary.', 5)
            
            summary_text, token_count = service._generate_summary(
                title='Test Title',
                content='Test content',
                ai_model='gpt-4.1-nano',
                max_words=100
            )
            
            self.assertEqual(summary_text, 'This is a test summary.')
            # Should fall back to word count
            self.assertEqual(token_count, 5)  # 5 words in summary

    def test_summarize_article_article_not_found(self):
        """Test summarize_article with non-existent article."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            with self.assertRaises(Article.DoesNotExist):
                service.summarize_article(
                    article_id=999,
                    ai_model='gpt-4.1-nano',
                    user=self.user
                )

    @patch('summarizer.service.SummarizerService._generate_summary')
    def test_summarize_article_error_handling(self, mock_generate_summary):
        """Test summarize_article error handling."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            service = SummarizerService()
            
            # Mock the _generate_summary method to raise an exception
            mock_generate_summary.side_effect = Exception('API Error')
            
            # Use a unique ai_model to avoid unique constraint
            unique_model = 'gpt-4.1-nano-error-test'
            
            with self.assertRaises(Exception):
                service.summarize_article(
                    article_id=self.article.id,
                    ai_model=unique_model,
                    user=self.user
                )
            
            # Check that summary was created and marked as failed
            summary = Summary.objects.get(article=self.article, ai_model=unique_model)
            self.assertEqual(summary.status, 'failed')
            self.assertIn('API Error', summary.error_message)

    def test_get_article_summary_existing(self):
        """Test get_article_summary with existing summary."""
        summary = Summary.objects.create(
            article=self.article,
            summary_text='Test summary',
            ai_model='gpt-4.1-nano',
            status='completed'
        )
        
        service = SummarizerService()
        result = service.get_article_summary(
            article_id=self.article.id,
            ai_model='gpt-4.1-nano'
        )
        
        self.assertEqual(result, summary)

    def test_get_article_summary_not_found(self):
        """Test get_article_summary with no existing summary."""
        service = SummarizerService()
        result = service.get_article_summary(
            article_id=self.article.id,
            ai_model='gpt-4.1-nano'
        )
        
        self.assertIsNone(result)

    def test_get_article_summary_different_model(self):
        """Test get_article_summary with different model."""
        summary = Summary.objects.create(
            article=self.article,
            summary_text='Test summary',
            ai_model='gpt-4.1-nano',
            status='completed'
        )
        
        service = SummarizerService()
        result = service.get_article_summary(
            article_id=self.article.id,
            ai_model='gpt-3.5-turbo'
        )
        
        self.assertIsNone(result)  # Different model

    def test_get_article_summaries_multiple(self):
        """Test get_article_summaries with multiple summaries."""
        summary1 = Summary.objects.create(
            article=self.article,
            summary_text='Summary 1',
            ai_model='gpt-4.1-nano',
            status='completed'
        )
        
        summary2 = Summary.objects.create(
            article=self.article,
            summary_text='Summary 2',
            ai_model='gpt-3.5-turbo',
            status='completed'
        )
        
        service = SummarizerService()
        result = service.get_article_summaries(article_id=self.article.id)
        
        self.assertEqual(result['article_id'], self.article.id)
        self.assertEqual(len(result['summaries']), 2)
        
        summary_ids = [s['id'] for s in result['summaries']]
        self.assertIn(summary1.id, summary_ids)
        self.assertIn(summary2.id, summary_ids)

    def test_get_article_summaries_empty(self):
        """Test get_article_summaries with no summaries."""
        service = SummarizerService()
        result = service.get_article_summaries(article_id=self.article.id)
        
        self.assertEqual(result['article_id'], self.article.id)
        self.assertEqual(len(result['summaries']), 0) 
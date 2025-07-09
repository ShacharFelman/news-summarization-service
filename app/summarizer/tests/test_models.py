from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from summarizer.models import Summary
from articles.models import Article
from datetime import datetime


class SummaryModelTest(TestCase):
    """Test cases for the Summary model."""

    def setUp(self):
        """Set up test data."""
        self.user = get_user_model().objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
        self.article = Article.objects.create(
            title='Test Article',
            content='This is a test article content for testing purposes.',
            url='http://example.com/test',
            published_date=timezone.now(),
            author='Test Author',
            source='Test Source',
            news_client_source='TestAPI'
        )

    def test_summary_creation(self):
        """Test creating a summary."""
        summary = Summary.objects.create(
            article=self.article,
            summary_text='This is a test summary.',
            ai_model='gpt-4.1-nano',
            status='completed',
            word_count=10,
            tokens_used=50,
            requested_by=self.user
        )
        
        self.assertEqual(summary.article, self.article)
        self.assertEqual(summary.summary_text, 'This is a test summary.')
        self.assertEqual(summary.ai_model, 'gpt-4.1-nano')
        self.assertEqual(summary.status, 'completed')
        self.assertEqual(summary.word_count, 10)
        self.assertEqual(summary.tokens_used, 50)
        self.assertEqual(summary.requested_by, self.user)

    def test_summary_default_values(self):
        """Test summary creation with default values."""
        summary = Summary.objects.create(
            article=self.article
        )
        
        self.assertEqual(summary.ai_model, 'openai-gpt-4.1-nano')
        self.assertEqual(summary.status, 'pending')
        self.assertIsNone(summary.summary_text)
        self.assertIsNone(summary.word_count)
        self.assertIsNone(summary.tokens_used)
        self.assertIsNone(summary.error_message)
        self.assertIsNone(summary.completed_at)

    def test_summary_status_properties(self):
        """Test summary status properties."""
        summary = Summary.objects.create(
            article=self.article,
            status='pending'
        )
        
        self.assertTrue(summary.is_pending)
        self.assertFalse(summary.is_completed)
        self.assertFalse(summary.is_failed)
        
        summary.status = 'completed'
        summary.save()
        
        self.assertTrue(summary.is_completed)
        self.assertFalse(summary.is_pending)
        self.assertFalse(summary.is_failed)
        
        summary.status = 'failed'
        summary.save()
        
        self.assertTrue(summary.is_failed)
        self.assertFalse(summary.is_completed)
        self.assertFalse(summary.is_pending)

    def test_summary_string_representation(self):
        """Test summary string representation."""
        summary = Summary.objects.create(
            article=self.article,
            summary_text='Test summary'
        )
        
        expected = f"Summary for: {self.article.title[:50]}..."
        self.assertEqual(str(summary), expected)

    def test_summary_ordering(self):
        """Test summary ordering by created_at descending."""
        summary1 = Summary.objects.create(
            article=self.article,
            ai_model='gpt-4.1-nano',
            created_at=timezone.now()
        )
        # Create second summary with later timestamp and different ai_model
        summary2 = Summary.objects.create(
            article=self.article,
            ai_model='gpt-3.5-turbo',
            created_at=timezone.now() + timezone.timedelta(hours=1)
        )
        summaries = Summary.objects.all()
        self.assertEqual(summaries[0], summary2)  # Most recent first
        self.assertEqual(summaries[1], summary1)

    def test_summary_unique_constraint(self):
        """Test that duplicate summaries for same article and model are prevented."""
        Summary.objects.create(
            article=self.article,
            ai_model='gpt-4.1-nano'
        )
        
        # Should not be able to create another summary with same article and model
        with self.assertRaises(Exception):
            Summary.objects.create(
                article=self.article,
                ai_model='gpt-4.1-nano'
            )

    def test_summary_with_different_models(self):
        """Test that summaries with different models can coexist for same article."""
        summary1 = Summary.objects.create(
            article=self.article,
            ai_model='gpt-4.1-nano'
        )
        
        summary2 = Summary.objects.create(
            article=self.article,
            ai_model='gpt-3.5-turbo'
        )
        
        self.assertNotEqual(summary1.id, summary2.id)
        self.assertEqual(summary1.article, summary2.article)
        self.assertNotEqual(summary1.ai_model, summary2.ai_model)

    def test_summary_without_user(self):
        """Test creating summary without a user."""
        summary = Summary.objects.create(
            article=self.article
        )
        
        self.assertIsNone(summary.requested_by)

    def test_summary_error_handling(self):
        """Test summary with error message."""
        summary = Summary.objects.create(
            article=self.article,
            status='failed',
            error_message='API rate limit exceeded'
        )
        
        self.assertTrue(summary.is_failed)
        self.assertEqual(summary.error_message, 'API rate limit exceeded')

    def test_summary_completion_timestamp(self):
        """Test summary completion timestamp."""
        summary = Summary.objects.create(
            article=self.article,
            status='pending'
        )
        
        self.assertIsNone(summary.completed_at)
        
        # Simulate completion
        completion_time = timezone.now()
        summary.status = 'completed'
        summary.completed_at = completion_time
        summary.save()
        
        self.assertEqual(summary.completed_at, completion_time)
        self.assertTrue(summary.is_completed) 
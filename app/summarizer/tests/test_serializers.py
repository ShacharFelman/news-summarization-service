from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from summarizer.models import Summary
from summarizer.serializers import SummarySerializer
from articles.models import Article


class SummarySerializerTest(TestCase):
    """Test cases for the SummarySerializer."""

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

    def test_summary_serializer_fields(self):
        """Test that serializer includes all expected fields."""
        serializer = SummarySerializer(self.summary)
        data = serializer.data
        
        expected_fields = [
            'id', 'ai_model', 'status', 'summary_text', 'word_count', 
            'tokens_used', 'created_at', 'completed_at', 'error_message'
        ]
        
        for field in expected_fields:
            self.assertIn(field, data)

    def test_summary_serializer_data(self):
        """Test that serializer returns correct data."""
        serializer = SummarySerializer(self.summary)
        data = serializer.data
        
        self.assertEqual(data['id'], self.summary.id)
        self.assertEqual(data['ai_model'], 'gpt-4.1-nano')
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['summary_text'], 'This is a test summary of the article.')
        self.assertEqual(data['word_count'], 15)
        self.assertEqual(data['tokens_used'], 75)
        self.assertIsNotNone(data['created_at'])
        self.assertIsNotNone(data['completed_at'])
        self.assertIsNone(data['error_message'])

    def test_summary_serializer_with_error(self):
        """Test serializer with failed summary."""
        failed_summary = Summary.objects.create(
            article=self.article,
            status='failed',
            error_message='API rate limit exceeded',
            ai_model='gpt-3.5-turbo'
        )
        
        serializer = SummarySerializer(failed_summary)
        data = serializer.data
        
        self.assertEqual(data['status'], 'failed')
        self.assertEqual(data['error_message'], 'API rate limit exceeded')
        self.assertEqual(data['ai_model'], 'gpt-3.5-turbo')
        self.assertIsNone(data['summary_text'])
        self.assertIsNone(data['word_count'])
        self.assertIsNone(data['tokens_used'])
        self.assertIsNone(data['completed_at'])

    def test_summary_serializer_pending_status(self):
        """Test serializer with pending summary."""
        pending_summary = Summary.objects.create(
            article=self.article,
            status='pending',
            ai_model='gpt-4'
        )
        
        serializer = SummarySerializer(pending_summary)
        data = serializer.data
        
        self.assertEqual(data['status'], 'pending')
        self.assertIsNone(data['summary_text'])
        self.assertIsNone(data['word_count'])
        self.assertIsNone(data['tokens_used'])
        self.assertIsNone(data['completed_at'])
        self.assertIsNone(data['error_message'])

    def test_summary_serializer_read_only_fields(self):
        """Test that all fields are read-only."""
        serializer = SummarySerializer(self.summary)
        
        # All fields should be read-only
        for field_name in serializer.fields:
            field = serializer.fields[field_name]
            self.assertTrue(field.read_only, f"Field {field_name} should be read-only")

    def test_summary_serializer_multiple_summaries(self):
        """Test serializing multiple summaries."""
        # Create another summary
        summary2 = Summary.objects.create(
            article=self.article,
            summary_text='Another test summary.',
            ai_model='gpt-3.5-turbo',
            status='completed',
            word_count=8,
            tokens_used=45
        )
        
        summaries = [self.summary, summary2]
        serializer = SummarySerializer(summaries, many=True)
        data = serializer.data
        
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['ai_model'], 'gpt-4.1-nano')
        self.assertEqual(data[1]['ai_model'], 'gpt-3.5-turbo')
        self.assertEqual(data[0]['summary_text'], 'This is a test summary of the article.')
        self.assertEqual(data[1]['summary_text'], 'Another test summary.')

    def test_summary_serializer_datetime_formatting(self):
        """Test that datetime fields are properly formatted."""
        serializer = SummarySerializer(self.summary)
        data = serializer.data
        
        # Check that datetime fields are strings (ISO format)
        self.assertIsInstance(data['created_at'], str)
        self.assertIsInstance(data['completed_at'], str)
        
        # Verify they can be parsed as ISO format
        from datetime import datetime
        datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        datetime.fromisoformat(data['completed_at'].replace('Z', '+00:00')) 
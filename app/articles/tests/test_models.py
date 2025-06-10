"""
Tests for Article model validation and behavior.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
from articles.models import Article

class TestArticleModel(TestCase):
    """Test suite for the Article model."""

    def setUp(self):
        self.valid_article_data = {
            'title': 'Test Article',
            'content': 'This is a test article content.',
            'url': 'http://example.com/test-article',
            'published_date': timezone.now(),
            'source': 'Example News'
        }

    def test_creation_with_valid_data(self):
        """Article can be created with valid data."""
        article = Article.objects.create(**self.valid_article_data)

        self.assertIsNotNone(article.id)
        self.assertEqual(article.title, self.valid_article_data['title'])
        self.assertEqual(article.content, self.valid_article_data['content'])
        self.assertEqual(article.url, self.valid_article_data['url'])
        self.assertEqual(article.published_date, self.valid_article_data['published_date'])
        self.assertEqual(article.source, self.valid_article_data['source'])

    def test_field_constraints_and_validation(self):
        """Field validations work as expected."""
        invalid_data = self.valid_article_data.copy()
        invalid_data['url'] = 'invalid_url'
        article = Article(**invalid_data)
        with self.assertRaises(ValidationError):
            article.full_clean()

        # Test required fields
        required_fields = ['title', 'content', 'url', 'published_date', 'source']
        for field in required_fields:
            invalid_data = self.valid_article_data.copy()
            invalid_data[field] = None
            article = Article(**invalid_data)
            with self.assertRaises(ValidationError):
                article.full_clean()

        # Test URL uniqueness
        Article.objects.create(**self.valid_article_data)
        duplicate = Article(**self.valid_article_data)
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_str_representation(self):
        """Article string representation is its title."""
        article = Article.objects.create(**self.valid_article_data)
        self.assertEqual(str(article), self.valid_article_data['title'])

    def test_article_ordering(self):
        """Articles are ordered by published_date in descending order."""
        now = timezone.now()
        # Create articles with different published dates
        old_article = Article.objects.create(
            title='Old Article',
            content='Old content',
            url='http://example.com/old',
            published_date=now - datetime.timedelta(days=2),
            source='Test'
        )
        new_article = Article.objects.create(
            title='New Article',
            content='New content',
            url='http://example.com/new',
            published_date=now,
            source='Test'
        )
        middle_article = Article.objects.create(
            title='Middle Article',
            content='Middle content',
            url='http://example.com/middle',
            published_date=now - datetime.timedelta(days=1),
            source='Test'
        )

        # Get ordered articles
        articles = Article.objects.all()

        # Verify ordering
        self.assertEqual(articles[0], new_article)
        self.assertEqual(articles[1], middle_article)
        self.assertEqual(articles[2], old_article)

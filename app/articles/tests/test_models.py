from django.test import TestCase
from django.core.exceptions import ValidationError
from articles.models import Article
import datetime

class TestArticleModel(TestCase):
    def setUp(self):
        self.valid_article_data = {
            'title': 'Test Article',
            'content': 'This is a test article content.',
            'url': 'http://example.com/test-article',
            'published_date': datetime.date.today(),
            'source': 'Example News'
        }

    def test_article_creation_valid_data(self):
        # Create an article with valid data and ensure it's saved correctly.
        article = Article.objects.create(**self.valid_article_data)
        self.assertIsNotNone(article.id)
        self.assertEqual(article.title, self.valid_article_data['title'])
        self.assertEqual(article.content, self.valid_article_data['content'])
        self.assertEqual(article.url, self.valid_article_data['url'])
        self.assertEqual(article.published_date, self.valid_article_data['published_date'])
        self.assertEqual(article.source, self.valid_article_data['source'])

    def test_article_field_validations(self):
        # Test URL validation: using an invalid URL should trigger a ValidationError.
        invalid_data = self.valid_article_data.copy()
        invalid_data['url'] = 'invalid_url'
        article = Article(**invalid_data)
        with self.assertRaises(ValidationError):
            article.full_clean()

        # Test non-null field: title should not be None.
        missing_title_data = self.valid_article_data.copy()
        missing_title_data['title'] = None
        article = Article(**missing_title_data)
        with self.assertRaises(ValidationError):
            article.full_clean()

    def test_article_str_representation(self):
        # Assuming the __str__ method returns the article's title.
        article = Article.objects.create(**self.valid_article_data)
        self.assertEqual(str(article), self.valid_article_data['title'])

from django.test import TestCase
from articles.models import Article
from articles.serializers import ArticleSerializer
from django.utils import timezone


def create_article(**params):
    """Create a sample article with default or provided parameters."""
    defaults = {
            'title': 'Test Article',
            'content': 'This is test content for the article.',
            'url': 'http://example.com/article',
            'published_date': timezone.now(),
            'source': 'Example Source'
        }
    defaults.update(params)

    return defaults


class TestArticleSerializer(TestCase):
    def setUp(self):
        """Create an article instance for serialization tests."""
        self.valid_article_data = create_article()
        self.article = Article.objects.create(**self.valid_article_data)

    def test_article_serialization(self):
        """Validate that the serializer correctly serializes an Article instance."""
        serializer = ArticleSerializer(self.article)
        data = serializer.data
        self.assertEqual(data['title'], self.valid_article_data['title'])
        self.assertEqual(data['content'], self.valid_article_data['content'])
        self.assertEqual(data['url'], self.valid_article_data['url'])
        self.assertEqual(data['published_date'], self.valid_article_data['published_date'].isoformat().replace('+00:00', 'Z'))
        self.assertEqual(data['source'], self.valid_article_data['source'])

    def test_article_deserialization_valid_data(self):
        """Test that valid JSON data can be deserialized into an Article instance."""
        new_article = create_article(url='http://example.com/article-2')

        serializer = ArticleSerializer(data=new_article)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        article = serializer.save()
        self.assertEqual(article.title, new_article['title'])
        self.assertEqual(article.content, new_article['content'])
        self.assertEqual(article.url, new_article['url'])
        self.assertEqual(article.published_date, new_article['published_date'])
        self.assertEqual(article.source, new_article['source'])

    def test_article_deserialization_invalid_data(self):
        """Test that missing required fields trigger validation errors."""
        invalid_data = self.valid_article_data.copy()

        invalid_data.pop('title')
        serializer = ArticleSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

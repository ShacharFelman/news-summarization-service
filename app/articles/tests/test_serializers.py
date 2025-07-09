from django.test import TestCase
from django.utils import timezone
from articles.serializers import ArticleSerializer
from articles.models import Article

class ArticleSerializerTest(TestCase):
    def setUp(self):
        self.valid_data = {
            'title': 'Test Article',
            'content': 'Some content',
            'url': 'http://example.com/article',
            'published_date': timezone.now(),
            'author': 'Author Name',
            'source': 'Test Source',
            'news_client_source': 'Test Client'
        }

    def test_valid_serializer(self):
        serializer = ArticleSerializer(data=self.valid_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_published_date_in_future(self):
        data = self.valid_data.copy()
        data['published_date'] = timezone.now() + timezone.timedelta(days=1)
        serializer = ArticleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('published_date', serializer.errors)

    def test_missing_required_fields(self):
        data = self.valid_data.copy()
        data.pop('title')
        serializer = ArticleSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors) 
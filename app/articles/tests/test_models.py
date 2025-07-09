from django.test import TestCase
from django.utils import timezone
from articles.models import Article

class ArticleModelTest(TestCase):
    def setUp(self):
        self.article = Article.objects.create(
            title="Test Article",
            content="Some content",
            url="http://example.com/article",
            published_date=timezone.now(),
            author="Author Name",
            source="Test Source",
            news_client_source="Test Client"
        )

    def test_str_representation(self):
        self.assertEqual(str(self.article), self.article.title)

    def test_ordering(self):
        article2 = Article.objects.create(
            title="Second Article",
            content="More content",
            url="http://example.com/article2",
            published_date=timezone.now() + timezone.timedelta(days=1),
            author="Author 2",
            source="Source 2",
            news_client_source="Client 2"
        )
        articles = Article.objects.all()
        self.assertEqual(articles[0], article2)
        self.assertEqual(articles[1], self.article)

    def test_field_constraints(self):
        # url must be unique
        with self.assertRaises(Exception):
            Article.objects.create(
                title="Duplicate URL",
                content="Content",
                url="http://example.com/article",
                published_date=timezone.now(),
                author="Author",
                source="Source",
                news_client_source="Client"
            ) 
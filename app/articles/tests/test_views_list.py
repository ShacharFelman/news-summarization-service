from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User

class ArticleViewSetListTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@example.com', password='testpass', name='Test User')
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

    def test_list_articles_unauthenticated(self):
        url = reverse('articles:articles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_list_articles_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('articles:articles-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 1)

    def test_retrieve_article_unauthenticated(self):
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_retrieve_article_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], self.article.id) 
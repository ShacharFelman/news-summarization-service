from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User
from django.core.cache import cache
import time

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

    def test_list_articles_caching(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        url = reverse('articles:articles-list')
        cache.clear()
        start = time.time()
        response1 = self.client.get(url)
        uncached_time = time.time() - start
        self.assertEqual(response1.status_code, 200)
        start = time.time()
        response2 = self.client.get(url)
        cached_time = time.time() - start
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(response1.data, response2.data)
        # Cached response should be faster (not strict, but usually true)
        self.assertLess(cached_time, uncached_time * 0.8 + 0.05) 
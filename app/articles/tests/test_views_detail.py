from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User
from django.core.cache import cache
import time

class ArticleViewSetDetailTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@example.com', password='adminpass', name='Admin User', is_staff=True)
        self.admin_token = Token.objects.create(user=self.user)
        self.regular_user = User.objects.create_user(email='user@example.com', password='userpass', name='Regular User')
        self.user_token = Token.objects.create(user=self.regular_user)
        self.article = Article.objects.create(
            title="Test Article",
            content="Some content",
            url="http://example.com/article",
            published_date=timezone.now(),
            author="Author Name",
            source="Test Source",
            news_client_source="Test Client"
        )

    def test_update_article_unauthenticated(self):
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.put(url, {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_update_article_authenticated_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.put(url, {'title': 'Updated'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_update_article_authenticated_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
        data = {
            'title': 'Updated',
            'content': self.article.content,
            'url': self.article.url,
            'published_date': self.article.published_date,
            'author': self.article.author,
            'source': self.article.source,
            'news_client_source': self.article.news_client_source
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, 'Updated')

    def test_delete_article_unauthenticated(self):
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_delete_article_authenticated_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_delete_article_authenticated_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Article.objects.filter(id=self.article.id).exists())

    def test_retrieve_article_caching(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('articles:articles-detail', args=[self.article.id])
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
        self.assertLess(cached_time, uncached_time * 0.8 + 0.05)

    def test_summary_article_caching(self):
        # This test is no longer relevant as caching is not applied to the async summary endpoint.
        pass 
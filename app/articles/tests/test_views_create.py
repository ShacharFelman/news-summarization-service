from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from articles.models import Article
from users.models import User

class ArticleViewSetCreateTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='admin@example.com', password='adminpass', name='Admin User', is_staff=True)
        self.admin_token = Token.objects.create(user=self.user)
        self.regular_user = User.objects.create_user(email='user@example.com', password='userpass', name='Regular User')
        self.user_token = Token.objects.create(user=self.regular_user)
        self.valid_data = {
            'title': 'New Article',
            'content': 'Some content',
            'url': 'http://example.com/new-article',
            'published_date': timezone.now(),
            'author': 'Author',
            'source': 'Source',
            'news_client_source': 'Client'
        }

    def test_create_article_unauthenticated(self):
        url = reverse('articles:articles-list')
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_article_authenticated_non_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.user_token.key}')
        url = reverse('articles:articles-list')
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, 403)

    def test_create_article_authenticated_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('articles:articles-list')
        response = self.client.post(url, self.valid_data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Article.objects.count(), 1)

    def test_create_article_invalid(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        url = reverse('articles:articles-list')
        data = self.valid_data.copy()
        data['published_date'] = timezone.now() + timezone.timedelta(days=1)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('published_date', response.data) 
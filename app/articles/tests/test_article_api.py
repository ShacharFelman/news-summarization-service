# from django.test import TestCase
# from django.utils import timezone
# from django.contrib.auth import get_user_model
# from django.core.cache import cache
# from django.urls import reverse
# from unittest.mock import patch
# from rest_framework import status
# from rest_framework.test import APIClient

# from articles.models import Article
# import datetime

# User = get_user_model()


# def create_article(**params):
#     """Helper to create and return an Article instance."""
#     defaults = {
#         'title': 'Sample Article',
#         'content': 'Sample content for testing.',
#         'url': 'http://example.com/sample',
#         'published_date': timezone.now(),
#         'source': 'Test Source'
#     }
#     defaults.update(params)
#     return Article.objects.create(**defaults)


# class TestArticleEndpoints(TestCase):
#     """Test suite for the Article API endpoints."""

#     def setUp(self):
#         """Set up test environment, create a user and authenticate."""
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpassword'
#         )
#         self.client = APIClient()
#         self.client.force_authenticate(user=self.user)

#         # Clear cache before each test
#         cache.clear()

#     #======================================
#     # 1. GET /articles/  (Paginated list)
#     #======================================

#     def test_list_articles_authenticated_returns_paginated(self):
#         """Test that the list articles endpoint returns paginated results for authenticated users."""
#         # Create 12 articles to exceed default page_size=10
#         for i in range(12):
#             create_article(
#                 title=f'Article {i}',
#                 url=f'http://example.com/{i}',
#                 published_date=timezone.now() - datetime.timedelta(days=i)
#             )

#         response = self.client.get('/articles/?page=1')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#         data = response.json()
#         self.assertIn('count', data)
#         self.assertIn('next', data)
#         self.assertIn('previous', data)
#         self.assertIn('results', data)
#         self.assertEqual(data['count'], 12)
#         # page_size assumed to be 10
#         self.assertEqual(len(data['results']), 10)
#         self.assertIsNotNone(data['next'])
#         self.assertIsNone(data['previous'])

#         # Test second page
#         next_url = data['next']
#         response_page2 = self.client.get(next_url)
#         self.assertEqual(response_page2.status_code, status.HTTP_200_OK)
#         data2 = response_page2.json()
#         # Remaining 2 articles
#         self.assertEqual(len(data2['results']), 2)
#         self.assertIsNone(data2['next'])
#         self.assertIsNotNone(data2['previous'])

#     def test_list_articles_unauthenticated_returns_401(self):
#         """Test that unauthenticated users receive a 401 response."""
#         # Use a fresh client without authentication
#         client = APIClient()
#         response = client.get('/articles/')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertIn('detail', response.json())

#     def test_list_articles_page_out_of_range_returns_404(self):
#         """Test that requesting a page out of range returns 404."""
#         # Only 3 articles in DB
#         for i in range(3):
#             create_article(
#                 title=f'Article {i}',
#                 url=f'http://example.com/out/{i}'
#             )

#         response = self.client.get('/articles/?page=5')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     #======================================
#     # 2. GET /articles/<id>/  (Detail view)
#     #======================================

#     def test_retrieve_article_authenticated_returns_200(self):
#         article = create_article(
#             title='Detail Article',
#             url='http://example.com/detail'
#         )
#         response = self.client.get(f'/articles/{article.id}/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#         data = response.json()
#         self.assertEqual(data['id'], article.id)
#         self.assertEqual(data['title'], article.title)
#         self.assertEqual(data['content'], article.content)
#         self.assertEqual(data['url'], article.url)
#         self.assertIn('published_date', data)
#         self.assertEqual(data['source'], article.source)

#     def test_retrieve_article_unauthenticated_returns_401(self):
#         article = create_article()
#         client = APIClient()
#         response = client.get(f'/articles/{article.id}/')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertIn('detail', response.json())

#     def test_retrieve_article_not_found_returns_404(self):
#         response = self.client.get('/articles/9999/')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     #===============================================
#     # 3. GET /articles/<id>/summary/  (Summary view)
#     #===============================================

#     def test_summary_cached_returns_cached_without_calling_service(self):
#         article = create_article(
#             title='Cache Hit',
#             url='http://example.com/cached'
#         )
#         cache_key = f'article_summary:{article.id}'
#         cache.set(cache_key, 'Existing cached summary')

#         response = self.client.get(f'/articles/{article.id}/summary/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#         data = response.json()
#         self.assertEqual(data.get('summary'), 'Existing cached summary')

#         # Ensure summarization service is not called
#         with patch('summarization.services.generate_summary') as mock_generate:
#             self.assertFalse(mock_generate.called)

#     @patch('summarization.services.generate_summary')
#     def test_summary_cache_miss_generates_and_caches(self, mock_generate):
#         article = create_article(
#             title='Cache Miss',
#             url='http://example.com/miss'
#         )
#         cache_key = f'article_summary:{article.id}'
#         self.assertIsNone(cache.get(cache_key))

#         mock_generate.return_value = 'Generated summary text'

#         response = self.client.get(f'/articles/{article.id}/summary/')
#         self.assertEqual(response.status_code, status.HTTP_200_OK)

#         data = response.json()
#         self.assertEqual(data.get('summary'), 'Generated summary text')

#         # After request, summary should be cached
#         self.assertEqual(cache.get(cache_key), 'Generated summary text')
#         mock_generate.assert_called_once_with(article)

#     def test_summary_unauthenticated_returns_401(self):
#         article = create_article()
#         client = APIClient()
#         response = client.get(f'/articles/{article.id}/summary/')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertIn('detail', response.json())

#     def test_summary_article_not_found_returns_404(self):
#         response = self.client.get('/articles/9999/summary/')
#         self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

#     #
#     # 4. POST /articles/  (Create view)
#     #

#     def test_create_article_authenticated_valid_returns_201(self):
#         payload = {
#             "title": "Breaking News",
#             "content": "Full text of the article.",
#             "url": "http://unique.com/1",
#             "published_date": (timezone.now() - datetime.timedelta(hours=1)).isoformat().replace('+00:00', 'Z'),
#             "source": "News API"
#         }
#         response = self.client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)

#         data = response.json()
#         self.assertIn('id', data)
#         self.assertEqual(data['title'], payload['title'])
#         self.assertEqual(data['content'], payload['content'])
#         self.assertEqual(data['url'], payload['url'])
#         self.assertEqual(data['published_date'], payload['published_date'])
#         self.assertEqual(data['source'], payload['source'])

#         # Verify in database
#         created = Article.objects.get(id=data['id'])
#         self.assertEqual(created.url, payload['url'])

#     def test_create_article_unauthenticated_returns_401(self):
#         client = APIClient()
#         payload = {
#             "title": "Unauthorized Create",
#             "content": "Should not be created.",
#             "url": "http://unique.com/unauth",
#             "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
#             "source": "News API"
#         }
#         response = client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertIn('detail', response.json())

#     def test_create_article_missing_field_returns_400(self):
#         payload = {
#             # "title" omitted
#             "content": "Missing title field.",
#             "url": "http://unique.com/2",
#             "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
#             "source": "News API"
#         }
#         response = self.client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         data = response.json()
#         self.assertIn('title', data)
#         self.assertEqual(data['title'], ["This field is required."])

#     def test_create_article_invalid_url_returns_400(self):
#         payload = {
#             "title": "Invalid URL Example",
#             "content": "Content here.",
#             "url": "not-a-valid-url",
#             "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
#             "source": "News API"
#         }
#         response = self.client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         data = response.json()
#         self.assertIn('url', data)

#     def test_create_article_duplicate_url_returns_400(self):
#         # First create an article with this URL
#         create_article(
#             title="Original",
#             url="http://duplicate.com/1",
#             published_date=timezone.now() - datetime.timedelta(days=1)
#         )

#         payload = {
#             "title": "Duplicate Attempt",
#             "content": "Trying to reuse URL.",
#             "url": "http://duplicate.com/1",
#             "published_date": timezone.now().isoformat().replace('+00:00', 'Z'),
#             "source": "News API"
#         }
#         response = self.client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         data = response.json()
#         self.assertIn('url', data)

#     def test_create_article_future_published_date_returns_400(self):
#         future_time = (timezone.now() + datetime.timedelta(days=30)).isoformat().replace('+00:00', 'Z')
#         payload = {
#             "title": "Future Article",
#             "content": "This date is in the future.",
#             "url": "http://unique.com/3",
#             "published_date": future_time,
#             "source": "News API"
#         }
#         response = self.client.post('/articles/', payload, format='json')
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

#         data = response.json()
#         self.assertIn('published_date', data)

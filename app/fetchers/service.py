"""NewsAPI fetcher implementation."""
import os
from typing import Dict, Any
import httpx
from django.utils.dateparse import parse_datetime
from .exceptions import ConfigurationError, FetcherError

class NewsApiFetcher():
    """
    Flexible fetcher for NewsAPI.org, driven by JSON config.
    Implements the BaseFetcher interface.
    """
    def __init__(self):
        api_key = os.environ.get('NEWSAPI_API_KEY')
        if not api_key:
            raise ConfigurationError("Missing api_key for NewsAPIFetcher. Provide it in environment or settings file.")
        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/top-headlines'

    def _get_query_params(self) -> Dict[str, Any]:
        """
        Returns the default query parameters for the NewsAPI endpoint.
        This can be overridden by passing custom parameters to the fetch method.
        """
        return {
            'language': 'en',
            'category': 'technology',
        }

    def _fetch_articles(self, query_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Perform the API call and return the raw response data from NewsAPI for the given endpoint.
        Ensures the api_key is included in the request parameters.
        """
        if not query_params:
            query_params = self._get_query_params()

        url = self.base_url
        query_params['apiKey'] = self.api_key

        try:
            response = httpx.get(url, params=query_params, timeout=15.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise FetcherError(f"Failed to fetch from NewsAPI: {e}")


    def _process_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the raw response data from NewsAPI and return a structured format.
        """
        if 'articles' not in response_data:
            raise FetcherError("Invalid response format from NewsAPI: 'articles' key missing")

        articles = response_data['articles']
        return {
            'status': response_data.get('status', 'unknown'),
            'totalResults': response_data.get('totalResults', 0),
            'articles': articles
        }

    def _save_articles(self, articles_data: list) -> None:
        """
        Save the fetched articles to the database.
        Skip articles that already exist (based on URL).
        """
        from articles.models import Article
        for article_data in articles_data:
            try:
                # Skip if article with this URL already exists
                if Article.objects.filter(url=article_data.get('url')).exists():
                    continue

                Article.objects.create(
                    title=article_data.get('title', ''),
                    content=article_data.get('content', ''),
                    url=article_data.get('url', ''),
                    published_date=parse_datetime(article_data.get('publishedAt')),
                    author=article_data.get('author'),
                    source=article_data.get('source', {}).get('name', 'Unknown'),
                    image_url=article_data.get('urlToImage'),
                    description=article_data.get('description'),
                    news_client_source='NewsAPI'
                )
            except Exception as e:
                print(f"Error saving article: {e}")

    def fetch_and_save(self, query_params: Dict[str, Any] = None):
        """
        Fetch articles from NewsAPI, save them to the database, and return the processed data.
        Optionally accepts custom query parameters to override defaults.
        """
        response_data = self._fetch_articles(query_params)
        if not response_data:
            raise FetcherError("No data returned from NewsAPI")

        processed_data = self._process_response(response_data)

        # Save articles to the database
        self._save_articles(processed_data['articles'])

        return processed_data

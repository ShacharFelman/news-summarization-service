import requests
from .base import BaseNewsFetcher

class NewsAPIFetcher(BaseNewsFetcher):
    ENDPOINTS = {
        'top-headlines': 'https://newsapi.org/v2/top-headlines',
        'everything': 'https://newsapi.org/v2/everything',
        'sources': 'https://newsapi.org/v2/sources',
    }

    # Valid options per endpoint (extracted from docs)
    VALID_PARAMS = {
        'top-headlines': {
            'country', 'category', 'sources', 'q', 'pageSize', 'page', 'language',
        },
        'everything': {
            'q', 'sources', 'domains', 'excludeDomains', 'from', 'to', 'language', 'sortBy', 'pageSize', 'page',
        },
        'sources': {
            'category', 'language', 'country',
        },
    }

    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_articles(self, endpoint='top-headlines', **options):
        """
        Fetches articles from NewsAPI.org, supports top-headlines, everything, sources endpoints.
        Options: all parameters from NewsAPI documentation.
        """
        if endpoint not in self.ENDPOINTS:
            raise ValueError(f"Unsupported endpoint: {endpoint}")

        url = self.ENDPOINTS[endpoint]
        params = {
            k: v for k, v in options.items() if k in self.VALID_PARAMS[endpoint]
        }
        params['apiKey'] = self.api_key

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # The format is different for sources endpoint
        if endpoint == 'sources':
            return data.get('sources', [])
        else:
            # Standardize article fields
            articles = []
            for item in data.get('articles', []):
                articles.append({
                    'title': item.get('title'),
                    'content': item.get('content') or item.get('description'),
                    'url': item.get('url'),
                    'published_date': item.get('publishedAt'),
                    'source': 'newsapi'
                })
            return articles

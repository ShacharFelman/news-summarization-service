"""NewsAPI fetcher implementation."""
import os
from typing import Dict, Any
import httpx
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

    def fetch_and_save(self, query_params: Dict[str, Any] = None):
        """
        Fetch articles from NewsAPI and return the processed data.
        Optionally accepts custom query parameters to override defaults.
        """
        response_data = self._fetch_articles(query_params)
        if not response_data:
            raise FetcherError("No data returned from NewsAPI")

        # Save response data to json file
        output_file = 'newsapi_response.json'
        with open(output_file, 'w') as f:
            import json
            json.dump(response_data, f, indent=4)
        print(f"Response data saved to {output_file}")

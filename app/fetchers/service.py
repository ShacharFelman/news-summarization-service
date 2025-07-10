"""NewsAPI fetcher implementation with FetchLog integration."""
import os
import json
from typing import Dict, Any, Tuple
import httpx
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from .exceptions import ConfigurationError, FetcherError
from fetchers.models import FetchLog


class NewsApiFetcher():
    """
    Flexible fetcher for NewsAPI.org, driven by JSON config.
    Implements the BaseFetcher interface with integrated FetchLog support.
    """
    def __init__(self, config: Dict[str, Any] = None):
        # Support both environment variable and config parameter
        api_key = None
        if config and 'api_key' in config:
            api_key = config['api_key']
        else:
            api_key = os.environ.get('NEWSAPI_API_KEY')

        if not api_key:
            raise ConfigurationError("Missing api_key for NewsAPIFetcher. Provide it in environment or config.")

        self.api_key = api_key
        self.base_url = 'https://newsapi.org/v2/top-headlines'
        self.config = config or {}

    def _get_query_params(self) -> Dict[str, Any]:
        """
        Returns the default query parameters for the NewsAPI endpoint.
        This can be overridden by passing custom parameters to the fetch method.
        """
        default_params = {
            'language': 'en',
            'category': 'technology',
        }

        # Override with config if provided
        if self.config:
            default_params.update({
                k: v for k, v in self.config.items()
                if k not in ['api_key']  # Exclude api_key from query params
            })

        return default_params

    def _create_fetch_log(self, source: str = 'NewsClientFetcher',
                         query_params: Dict[str, Any] = None) -> FetchLog:
        """Create a new FetchLog entry for this fetch operation."""
        from fetchers.models import FetchLog

        return FetchLog.objects.create(
            source=source,
            status=FetchLog.Status.PENDING,
            query_params=query_params or {},
            metadata={'fetcher_class': 'NewsApiFetcher'}
        )

    def _save_raw_data(self, fetch_log: 'FetchLog', raw_data: Dict[str, Any]) -> None:
        """Save raw response data to file and update fetch log."""
        if not raw_data:
            return

        try:
            # Create a filename based on fetch log ID and timestamp
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f"newsapi_raw_{fetch_log.id}_{timestamp}.json"

            # You might want to configure this path in settings
            raw_data_dir = os.path.join('media', 'raw_data')
            os.makedirs(raw_data_dir, exist_ok=True)

            file_path = os.path.join(raw_data_dir, filename)

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(raw_data, f, indent=2, ensure_ascii=False)

            fetch_log.raw_data_file = file_path
            fetch_log.save(update_fields=['raw_data_file'])

        except Exception as e:
            print(f"Warning: Could not save raw data file: {e}")

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

    def _save_articles(self, articles_data: list) -> Tuple[int, int]:
        """
        Save the fetched articles to the database.
        Skip articles that already exist (based on URL).

        Returns:
            Tuple[int, int]: (articles_processed, articles_saved)
        """
        from articles.models import Article

        articles_processed = 0
        articles_saved = 0

        for article_data in articles_data:
            articles_processed += 1
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
                articles_saved += 1

            except Exception as e:
                print(f"Error saving article: {e}")

        return articles_processed, articles_saved

    def fetch_and_save(self, query_params: Dict[str, Any] = None,
                      source: str = 'NewsClientFetcher'):
        """
        Fetch articles from NewsAPI, save them to the database, and return the processed data.
        Optionally accepts custom query parameters to override defaults.
        Now includes comprehensive FetchLog integration.
        """
        from fetchers.models import FetchLog

        # Use provided query params or get defaults
        if not query_params:
            query_params = self._get_query_params()

        # Create fetch log entry
        fetch_log = self._create_fetch_log(source, query_params)

        try:
            # Update status to in progress
            fetch_log.status = FetchLog.Status.IN_PROGRESS
            fetch_log.save(update_fields=['status'])

            # Fetch update_last_fetch() from API
            response_data = self._fetch_articles(query_params)
            if not response_data:
                raise FetcherError("No data returned from NewsAPI")

            # Save raw data to file
            # self._save_raw_data(fetch_log, response_data)

            # Process the response
            processed_data = self._process_response(response_data)

            # Update fetch log with fetched count
            fetch_log.articles_fetched = len(processed_data['articles'])
            fetch_log.save(update_fields=['articles_fetched'])

            # Save articles to the database and get counts
            articles_processed, articles_saved = self._save_articles(processed_data['articles'])

            # Add save statistics to the result
            processed_data['articles_processed'] = articles_processed
            processed_data['articles_saved'] = articles_saved
            processed_data['duplicates_skipped'] = articles_processed - articles_saved

            # Update fetch log metadata with additional info
            metadata = {
                'fetcher_class': 'NewsApiFetcher',
                'api_status': processed_data.get('status'),
                'total_results': processed_data.get('totalResults'),
                'duplicates_skipped': processed_data['duplicates_skipped']
            }

            # Complete the fetch log with success status
            fetch_log.complete(
                status=FetchLog.Status.SUCCESS,
                articles_saved=articles_saved,
                metadata=metadata
            )

            # # Update the source's last_fetch timestamp if provided
            # if source:
            #     source.update_last_fetch()

            return processed_data

        except Exception as e:
            # Log the error and mark fetch as failed
            error_message = str(e)
            fetch_log.complete(
                status=FetchLog.Status.ERROR,
                error_message=error_message,
                metadata={'fetcher_class': 'NewsApiFetcher', 'error_type': type(e).__name__}
            )

            # Re-raise the exception to maintain existing behavior
            raise e
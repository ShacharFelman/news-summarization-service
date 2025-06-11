import logging
import requests
from django.conf import settings
from .clients.newsapi import NewsAPIFetcher
from .exceptions import FetcherError

# Map of available fetcher classes. Extend this dict to add more sources.
NEWS_FETCHERS = {
    'newsapi': NewsAPIFetcher,
    # TODO: Add more sources here, e.g. 'nytimes': NYTimesFetcher
}

def get_fetcher(source_name: str):
    """
    Factory to create a fetcher instance by name.
    Raises FetcherError if the source is unknown.
    """
    if source_name in NEWS_FETCHERS:
        return NEWS_FETCHERS[source_name](settings.NEWSAPI_KEY)
    raise FetcherError(f"Unknown fetcher source: {source_name}")

def fetch_and_store_articles(source: str, options: dict) -> tuple:
    """
    Main service function.
    - Fetch articles from source
    - POST each to the articles API endpoint
    Returns (number_posted, total_fetched)
    """
    articles_api_url = settings.ARTICLES_API_URL
    try:
        fetcher = get_fetcher(source)
    except FetcherError:
        # Propagate FetcherError for unknown fetcher
        raise
    articles = fetcher.fetch_articles(**options)
    posted = 0
    if not articles:
        logging.warning(f"[fetchers] No articles fetched from source '{source}'.")
        return posted, 0
    for article in articles:
        try:
            resp = requests.post(articles_api_url, json=article, timeout=10)
            resp.raise_for_status()
            logging.info(f"[fetchers] Article '{article.get('title', 'N/A')}' posted successfully.")
            posted += 1
        except Exception as e:
            logging.error(f"[fetchers] Failed to post article '{article.get('title', 'N/A')}': {e}")
            # Do not raise, just continue
    logging.info(f"[fetchers] Finished posting articles: {posted}/{len(articles)} successful.")
    return posted, len(articles)

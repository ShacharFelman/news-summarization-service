from abc import ABC, abstractmethod

class BaseNewsFetcher(ABC):
    """
    Abstract interface for any news source fetcher.
    All fetchers must implement fetch_articles.
    """
    @abstractmethod
    def fetch_articles(self, **options):
        """
        Fetches articles from a source.
        Returns a list of dicts with at least:
        'title', 'content', 'url', 'published_date', 'source'
        """
        pass

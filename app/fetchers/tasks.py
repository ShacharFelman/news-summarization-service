from celery import shared_task
from .service import NewsApiFetcher

@shared_task(name='fetchers.tasks.fetch_articles_from_newsapi')
def fetch_articles_from_newsapi():
    """
    Celery task to fetch and save articles using NewsApiFetcher.
    """
    fetcher = NewsApiFetcher()
    fetcher.fetch_and_save()

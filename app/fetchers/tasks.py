from celery import shared_task
from django.utils import timezone
from django.db import transaction
from .service import NewsApiFetcher, FetcherError
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def fetch_articles_task(self, query_params=None):
    """
    Celery task to fetch articles from NewsAPI and save them to the database.
    This task will run periodically based on the schedule defined in celery.py
    """
    start_time = timezone.now()

    try:
        logger.info("Starting periodic article fetch task")

        # Initialize the fetcher
        fetcher = NewsApiFetcher()

        # Fetch and save articles
        result = fetcher.fetch_and_save(query_params)
        articles_fetched = result.get('totalResults', 0)

        logger.info(f"Successfully completed article fetch task. Total articles: {articles_fetched}")

        return {
            'status': 'success',
            'articles_count': articles_fetched,
            'fetch_time': start_time.isoformat()
        }

    except FetcherError as e:
        error_msg = f"Fetcher error: {str(e)}"
        logger.error(error_msg)

        # Retry the task
        try:
            raise self.retry(countdown=60, exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for fetch task: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'fetch_time': start_time.isoformat()
            }

    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)

        # Retry the task
        try:
            raise self.retry(countdown=60, exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for fetch task: {error_msg}")
            return {
                'status': 'failed',
                'error': error_msg,
                'fetch_time': start_time.isoformat()
            }

@shared_task
def test_task():
    """Test task to verify Celery is working correctly."""
    logger.info("Test task executed successfully")
    return "Test task completed"
from celery import shared_task
from django.utils import timezone
from .models import Summary
from articles.models import Article
from .service import SummarizerService
import logging
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def summarize_article_task(self, article_id, ai_model=None, user_id=None, max_words=150):
    """
    Celery task to summarize an article using AI in the background.
    Delegates all Summary model handling to the service layer.
    """
    from django.contrib.auth import get_user_model
    user = None
    if user_id:
        User = get_user_model()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            user = None
    try:
        service = SummarizerService()
        service.summarize_article(
            article_id=article_id,
            ai_model=ai_model,
            user=user,
            max_words=max_words
        )
        logger.info(f"Summary completed for article {article_id}")
    except Article.DoesNotExist:
        logger.error(f"Article {article_id} not found for summarization task.")
        # The service should handle status update if needed
    except Exception as e:
        logger.error(f"Error in summarize_article_task for article {article_id}: {e}")
        raise self.retry(exc=e, countdown=60) 
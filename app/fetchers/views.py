"""Views for the fetchers app."""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from fetchers.models import FetchLog
from fetchers.services import NewsService


class ArticleFetchView(APIView):
    """View for fetching articles from various sources."""

    async def post(self, request):
        """
        Trigger an article fetch operation.

        POST data:
            query: Search keywords
            source: Source ID (optional)
            language: Language code (default: en)
        """
        query = request.data.get('query')
        source = request.data.get('source')
        language = request.data.get('language', 'en')

        try:
            service = NewsService()
            fetch_log = await service.fetch_and_store(
                query=query,
                source=source,
                language=language
            )

            return Response({
                'id': fetch_log.id,
                'status': fetch_log.status,
                'articles_fetched': fetch_log.articles_fetched,
                'articles_saved': fetch_log.articles_saved,
                'error_message': fetch_log.error_message if fetch_log.error_message else None
            })

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
def fetch_status(request):
    """Get the status of recent article fetch operations."""
    recent_fetches = FetchLog.objects.filter(
        started_at__gte=timezone.now() - timezone.timedelta(days=1)
    ).order_by('-started_at')[:10]

    return Response([{
        'id': log.id,
        'fetch_type': log.fetch_type,
        'status': log.status,
        'started_at': log.started_at,
        'completed_at': log.completed_at,
        'articles_fetched': log.articles_fetched,
        'articles_saved': log.articles_saved,
        'error_message': log.error_message if log.error_message else None
    } for log in recent_fetches])
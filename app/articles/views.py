from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from news_service.permissions import IsAuthenticatedReadOnlyOrAdmin
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.authentication import TokenAuthentication

from articles.models import Article
from articles.serializers import ArticleSerializer
from summarizer.service import SummarizerService
from summarizer.serializers import SummarySerializer

import logging

logger = logging.getLogger(__name__)
class ArticleViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing articles.
    This viewset provides `list`, `create`, `retrieve`, `update`, and `destroy` actions.
    Methods:
        - GET: List all articles
        - POST: Create a new article
        - GET {id}/: Retrieve a specific article by ID
        - PUT {id}/: Update a specific article by ID
        - DELETE {id}/: Delete a specific article by ID

    * The articles are ordered by their published date in descending order.
    """

    queryset = Article.objects.all().order_by('-published_date')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticatedReadOnlyOrAdmin]
    authentication_classes = [TokenAuthentication]

    # Cache GET list endpoint (5 minutes)
    @method_decorator(cache_page(60 * 5), name='list')
    @method_decorator(cache_page(60 * 5), name='retrieve')
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @method_decorator(cache_page(60 * 5))
    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        """Fetch or generate a summary of an article asynchronously."""
        service = SummarizerService()
        # Ensure the article exists before calling the service
        try:
            Article.objects.get(id=pk)
        except Article.DoesNotExist:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            summary = service.summarize_article_async(article_id=pk, user=request.user if request.user.is_authenticated else None)
        except Article.DoesNotExist:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in ArticleViewSet.summary: {str(e)}")
            return Response({'error': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = SummarySerializer(summary)
        response_data = serializer.data
        if summary.status in ['pending', 'in_progress']:
            return Response({'success': True, 'summary': response_data, 'message': 'Summary is being processed.'}, status=status.HTTP_202_ACCEPTED)
        elif summary.status == 'completed':
            return Response({'success': True, 'summary': response_data}, status=status.HTTP_200_OK)
        elif summary.status == 'failed':
            return Response({'success': False, 'summary': response_data, 'message': 'Summary generation failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

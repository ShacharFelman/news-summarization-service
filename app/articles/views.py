from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

from articles.models import Article
from articles.serializers import ArticleSerializer
from summarizer.service import SummarizerService
from summarizer.serializers import SummarySerializer

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
    # permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        """Fetch or generate a summary of an article."""
        service = SummarizerService()
        try:
            summary = service.summarize_article(article_id=pk)
        except Article.DoesNotExist:
            return Response({'detail': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        serializer = SummarySerializer(summary)
        return Response(serializer.data)

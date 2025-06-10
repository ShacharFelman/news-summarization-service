from rest_framework import viewsets
# from rest_framework.permissions import IsAuthenticated

from articles.models import Article
from articles.serializers import ArticleSerializer

class ArticleViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing articles.
    This viewset provides `list`, `create`, `retrieve`, `update`, and `destroy` actions.
    The articles are ordered by their published date in descending order.
    """

    queryset = Article.objects.all().order_by('-published_date')
    serializer_class = ArticleSerializer
    # permission_classes = [IsAuthenticated]

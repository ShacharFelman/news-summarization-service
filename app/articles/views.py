from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from models import Article
from serializers import ArticleSerializer

class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """A viewset for viewing articles.
    This viewset provides `list` and `retrieve` actions for articles.
    It allows authenticated users to view the list of articles and retrieve
    individual articles by their ID.
    The articles are ordered by their published date in descending order.
    """

    queryset = Article.objects.all().order_by('-published_date')
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

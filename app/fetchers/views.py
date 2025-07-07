"""Views for the fetchers app."""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from fetchers.models import FetchLog
from fetchers.service import NewsApiFetcher, FetcherError


class ArticleFetchView(APIView):
    """View to manually trigger NewsApiFetcher.fetch_and_save."""
    def post(self, request):
        query_params = request.data.get('query_params', None)
        try:
            fetcher = NewsApiFetcher()
            fetcher.fetch_and_save(query_params)
            return Response({'message': 'Fetch and save completed successfully.'}, status=status.HTTP_200_OK)
        except FetcherError as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'error': f'Unexpected error: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



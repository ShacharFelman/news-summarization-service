"""Views for the fetchers app."""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from fetchers.service import NewsApiFetcher, FetcherError
from rest_framework.permissions import IsAdminUser
from rest_framework.authentication import TokenAuthentication

import logging
logger = logging.getLogger(__name__)


class ArticleFetchView(APIView):
    """View to manually trigger NewsApiFetcher.fetch_and_save."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        query_params = request.data.get('query_params', None)
        try:
            fetcher = NewsApiFetcher()
            fetcher.fetch_and_save(query_params, source='NewsClientFetcher')
            return Response({'message': 'Fetch and save completed successfully.'}, status=status.HTTP_200_OK)
        except FetcherError as e:
            logger.error(f"FetcherError in ArticleFetchView: {str(e)}")
            return Response({'error': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Unexpected error in ArticleFetchView: {str(e)}")
            return Response({'error': 'Internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



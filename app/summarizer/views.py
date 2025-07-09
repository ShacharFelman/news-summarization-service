from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from drf_spectacular.utils import extend_schema
from .service import SummarizerService
from .models import Summary
import json
import logging

logger = logging.getLogger(__name__)

class SummarizerView(APIView):
    """Base view for summarizer functionality."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.summarizer_service = SummarizerService()

@method_decorator(csrf_exempt, name='dispatch')
@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'article_id': {'type': 'integer'},
                'ai_model': {'type': 'string'},
                'max_words': {'type': 'integer'},
            },
            'required': ['article_id']
        }
    },
    responses={200: {'type': 'object'}}
)
class SummarizeArticleView(SummarizerView):
    """View to handle article summarization requests."""
    def post(self, request):
        """Create a new summary for an article."""
        article_id = request.data.get('article_id')
        ai_model = request.data.get('ai_model', 'openai-gpt-3.5-turbo')
        max_words = request.data.get('max_words', 150)
        if not article_id:
            return Response({'error': 'article_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None
        try:
            summary = self.summarizer_service.summarize_article(
                article_id=article_id,
                ai_model=ai_model,
                user=user,
                max_words=max_words
            )
            return Response({
                'success': True,
                'summary': {
                    'id': summary.id,
                    'article_id': summary.article.id,
                    'article_title': summary.article.title,
                    'summary_text': summary.summary_text,
                    'ai_model': summary.ai_model,
                    'status': summary.status,
                    'word_count': summary.word_count,
                    'tokens_used': summary.tokens_used,
                    'created_at': summary.created_at.isoformat(),
                    'completed_at': summary.completed_at.isoformat() if summary.completed_at else None
                }
            })
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in summarize view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(responses={200: {'type': 'object'}})
class GetSummaryView(SummarizerView):
    """View to retrieve existing summaries."""
    def get(self, request, article_id):
        """Get summary for a specific article."""
        ai_model = request.GET.get('ai_model', 'openai-gpt-3.5-turbo')
        try:
            summary = self.summarizer_service.get_article_summary(
                article_id=article_id,
                ai_model=ai_model
            )
            if not summary:
                return Response({'error': 'Summary not found'}, status=status.HTTP_404_NOT_FOUND)
            return Response({
                'success': True,
                'summary': {
                    'id': summary.id,
                    'article_id': summary.article.id,
                    'article_title': summary.article.title,
                    'summary_text': summary.summary_text,
                    'ai_model': summary.ai_model,
                    'status': summary.status,
                    'word_count': summary.word_count,
                    'tokens_used': summary.tokens_used,
                    'created_at': summary.created_at.isoformat(),
                    'completed_at': summary.completed_at.isoformat() if summary.completed_at else None
                }
            })
        except Exception as e:
            logger.error(f"Error in get summary view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(responses={200: {'type': 'object'}})
class GetAllSummariesView(SummarizerView):
    """View to retrieve all summaries for an article."""
    def get(self, request, article_id):
        """Get all summaries for a specific article."""
        try:
            summaries_data = self.summarizer_service.get_article_summaries(article_id)
            return Response({'success': True, 'data': summaries_data})
        except Exception as e:
            logger.error(f"Error in get all summaries view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.decorators import api_view

@extend_schema(responses={200: {'type': 'object'}})
@api_view(["GET"])
def summary_status(request, summary_id):
    """Get the status of a specific summary."""
    try:
        summary = Summary.objects.get(id=summary_id)
        return Response({
            'success': True,
            'status': {
                'id': summary.id,
                'status': summary.status,
                'created_at': summary.created_at.isoformat(),
                'completed_at': summary.completed_at.isoformat() if summary.completed_at else None,
                'error_message': summary.error_message
            }
        })
    except Summary.DoesNotExist:
        return Response({'error': 'Summary not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in summary status view: {str(e)}")
        return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
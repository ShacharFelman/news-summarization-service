from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from drf_spectacular.utils import extend_schema
from .service import SummarizerService
from .models import Summary
from .serializers import SummarySerializer
from articles.models import Article
import logging

logger = logging.getLogger(__name__)

class SummarizerView(APIView):
    """Base view for summarizer functionality."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

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
        """
        Create a new summary for an article. If a summary is being processed, return status 202 and 'in_progress' status.
        """
        article_id = request.data.get('article_id')
        ai_model = request.data.get('ai_model', 'gpt-4.1-nano')
        max_words = request.data.get('max_words', 150)
        if not article_id:
            return Response({'error': 'article_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None

        try:
            summary = self.summarizer_service.summarize_article_async(
                article_id=article_id,
                ai_model=ai_model,
                user=user,
                max_words=max_words
            )
        except Article.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return Response({'error': 'Invalid input.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in summarize view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = SummarySerializer(summary)
        response_data = serializer.data

        if summary.status in ['pending', 'in_progress']:
            return Response({'success': True, 'summary': response_data, 'message': 'Summary is being processed.'}, status=status.HTTP_202_ACCEPTED)
        elif summary.status == 'completed':
            return Response({'success': True, 'summary': response_data}, status=status.HTTP_200_OK)
        elif summary.status == 'failed':
            return Response({'success': False, 'summary': response_data, 'message': 'Summary generation failed.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(responses={200: {'type': 'object'}})
class GetSummaryView(SummarizerView):
    """View to retrieve existing summaries."""
    def get(self, request, article_id):
        """Get summary for a specific article."""
        ai_model = request.GET.get('ai_model', 'gpt-4.1-nano')
        try:
            summary = self.summarizer_service.get_article_summary(
                article_id=article_id,
                ai_model=ai_model
            )
            if not summary:
                try:
                    Article.objects.get(id=article_id)
                except Article.DoesNotExist:
                    return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
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
            try:
                Article.objects.get(id=article_id)
            except Article.DoesNotExist:
                return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)
            summaries_data = self.summarizer_service.get_article_summaries(article_id)
            return Response({'success': True, 'data': summaries_data})
        except Exception as e:
            logger.error(f"Error in get all summaries view: {str(e)}")
            return Response({'error': 'Internal server error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(responses={200: {'type': 'object'}})
@api_view(["GET"])
@permission_classes([IsAdminUser])
@authentication_classes([TokenAuthentication])
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
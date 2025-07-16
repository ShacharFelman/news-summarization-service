import logging
import os
from typing import Dict, Optional
from django.conf import settings
from django.utils import timezone

from .models import Summary
from articles.models import Article

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class SummarizerService:
    """Service for generating article summaries using OpenAI models via LangChain."""

    def __init__(self):
        # Prepare model mapping for future flexibility
        self.model_map = {
            "gpt-4.1-nano": "gpt-4.1-nano",
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "gpt-4-turbo": "gpt-4-turbo-preview",
        }
        self.default_model = "gpt-4.1-nano"
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", None)

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in Django settings")

        # Chat prompt template for summarization
        self.summarization_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                (
                    "You are an expert news summarizer. "
                    "Summarize the following article in up to {max_words} words, "
                    "focusing on the main points and key facts."
                ),
            ),
            (
                "user",
                (
                    "Title: {title}\n\n"
                    "Content: {content}\n\n"
                    "Summary:"
                ),
            ),
        ])

    def _get_llm(self, model_name: str = None):
        model = self.model_map.get(model_name, self.default_model)
        return ChatOpenAI(
            api_key=self.openai_api_key,
            model=model,
            temperature=0.3,
        )

    def summarize_article(
        self,
        article_id: int,
        ai_model: str = None,
        user=None,
        max_words: int = 150,
    ) -> Summary:
        """
        Summarize an article using AI.
        """
        try:
            article = Article.objects.get(id=article_id)
            model_key = ai_model or self.default_model

            # Check for existing completed summary
            summary = (
                Summary.objects.filter(article=article, ai_model=model_key, status="completed").first()
            )

            if summary:
                logger.info(f"Summary exists for article {article_id}")
                return summary

            # Create or reuse a summary record
            summary, _ = Summary.objects.get_or_create(
                article=article,
                ai_model=model_key,
                defaults={"status": "pending", "requested_by": user},
            )

            # Generate summary using LangChain
            summary_text, token_count = self._generate_summary(
                title=article.title,
                content=article.content,
                ai_model=model_key,
                max_words=max_words,
            )
            logger.info(f"Summarizing article {article_id} with model {model_key}")

            # Save result
            summary.summary_text = summary_text
            summary.tokens_used = token_count
            summary.word_count = len(summary_text.split())
            summary.status = "completed"
            summary.completed_at = timezone.now()
            summary.save()
            return summary

        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found")
            raise
        except Exception as e:
            logger.error(f"Error summarizing article {article_id}: {e}")
            if "summary" in locals():
                summary.status = "failed"
                summary.error_message = str(e)
                summary.save()
            raise

    def _generate_summary(
        self,
        title: str,
        content: str,
        ai_model: str,
        max_words: int,
    ) -> tuple[str, int]:
        """Use latest LangChain chain pattern for summarization."""
        llm = self._get_llm(ai_model)
        prompt = self.summarization_prompt

        chain = prompt | llm  # RunnableSequence: prompt → LLM

        # Use standardized dict input/output
        inputs = {"title": title, "content": content, "max_words": max_words}
        result = chain.invoke(inputs)

        # For ChatOpenAI, result.content holds the text
        summary_text = result.content if hasattr(result, "content") else str(result)

        # Get token usage if available
        token_count = getattr(result, "usage", {}).get("total_tokens", len(summary_text.split()))

        return summary_text.strip(), token_count

    def summarize_article_async(self, article_id: int, ai_model: str = None, user=None, max_words: int = 150) -> Summary:
        """
        Asynchronously summarize an article by enqueuing a Celery task.
        Returns the Summary object (status will be 'pending' or 'in_progress').
        """
        model_key = ai_model or self.default_model
        # Ensure the article exists, or raise Article.DoesNotExist
        try:
            article = Article.objects.get(id=article_id)
        except Article.DoesNotExist:
            logger.error(f"Article {article_id} not found (async)")
            raise
        # Check for existing completed summary
        summary = Summary.objects.filter(article=article, ai_model=model_key, status="completed").first()
        if summary:
            return summary
        summary, created = Summary.objects.get_or_create(
            article=article,
            ai_model=model_key,
            defaults={
                'status': 'pending',
                'requested_by': user
            }
        )
        # If already being processed or completed, return existing summary
        if not created and summary.status in ['pending', 'in_progress', 'completed']:
            return summary
        from .tasks import summarize_article_task
        summarize_article_task.delay(article_id, model_key, user.id if user else None, max_words)
        return summary

    def get_article_summary(self, article_id: int, ai_model: str = None) -> Optional[Summary]:
        model_key = ai_model or self.default_model
        return Summary.objects.filter(
            article_id=article_id,
            ai_model=model_key,
            status="completed"
        ).first()

    def get_article_summaries(self, article_id: int) -> Dict:
        summaries = Summary.objects.filter(article_id=article_id)
        return {
            "article_id": article_id,
            "summaries": [
                {
                    "id": s.id,
                    "ai_model": s.ai_model,
                    "status": s.status,
                    "summary_text": s.summary_text,
                    "word_count": s.word_count,
                    "tokens_used": s.tokens_used,
                    "created_at": s.created_at,
                    "completed_at": s.completed_at,
                    "error_message": s.error_message,
                }
                for s in summaries
            ],
        }

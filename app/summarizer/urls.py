from django.urls import path
from . import views

app_name = 'summarizer'

urlpatterns = [
    # POST /summarizer/summarize/ - Create new summary
    path('summarize/', views.SummarizeArticleView.as_view(), name='summarize_article'),

    # GET /summarizer/article/<int:article_id>/summary/ - Get specific summary
    path('article/<int:article_id>/summary/', views.GetSummaryView.as_view(), name='get_summary'),

    # GET /summarizer/article/<int:article_id>/summaries/ - Get all summaries for article
    path('article/<int:article_id>/summaries/', views.GetAllSummariesView.as_view(), name='get_all_summaries'),

    # GET /summarizer/summary/<int:summary_id>/status/ - Get summary status
    path('summary/<int:summary_id>/status/', views.summary_status, name='summary_status'),
]
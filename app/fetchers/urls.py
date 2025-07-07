"""URLs for the fetchers app."""
from django.urls import path
from . import views

app_name = 'fetchers'

urlpatterns = [
    path('fetch/', views.ArticleFetchView.as_view(), name='fetch_articles'),
]
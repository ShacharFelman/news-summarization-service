"""
URLs mapping for the articles app
"""


from django.urls import path
from rest_framework.routers import DefaultRouter

from articles import views

app_name = 'articles'

router = DefaultRouter()
router.register('', views.ArticleViewSet, basename='articles')

urlpatterns = router.urls + [
    path('<int:pk>/summary/', views.ArticleViewSet.as_view({'get': 'summary'}), name='articles-summary'),
]
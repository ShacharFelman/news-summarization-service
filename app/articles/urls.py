"""
URLs mapping for the articles app
"""


from rest_framework.routers import DefaultRouter

from articles import views

app_name = 'articles'

router = DefaultRouter()
router.register('', views.ArticleViewSet, basename='article')

urlpatterns = router.urls
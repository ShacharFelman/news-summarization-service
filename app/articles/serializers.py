from rest_framework import serializers
from django.utils import timezone
from .models import Article

class ArticleSerializer(serializers.ModelSerializer):
    def validate_published_date(self, value):
        """
        Check that the published date is not in the future.
        """
        if value > timezone.now():
            raise serializers.ValidationError("Published date cannot be in the future.")
        return value

    class Meta:
        model = Article
        fields = ['id', 'title', 'content', 'url', 'published_date', 'source']

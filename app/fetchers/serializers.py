"""Serializers for the fetchers app."""
from rest_framework import serializers
from .models import FetchLog
# from .models import NewsClientFetcher


# class NewsClientFetcherSerializer(serializers.ModelSerializer):
#     """Serializer for NewsClientFetcher model."""

#     class Meta:
#         model = NewsClientFetcher
#         fields = [
#             'id', 'name', 'is_active', 'class_path', 'config',
#             'fetch_interval', 'last_fetch', 'created_at', 'updated_at'
#         ]
#         read_only_fields = ['last_fetch', 'created_at', 'updated_at']


class FetchLogSerializer(serializers.ModelSerializer):
    """Serializer for FetchLog model."""

    source_name = serializers.CharField(source='source', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = FetchLog
        fields = [
            'id', 'source', 'source_name', 'status',
            'started_at', 'completed_at', 'articles_fetched',
            'articles_saved', 'error_message', 'query_params',
            'metadata', 'raw_data_file', 'duration'
        ]
        read_only_fields = fields

    def get_duration(self, obj):
        """Calculate the duration of the fetch operation."""
        if obj.completed_at and obj.started_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None
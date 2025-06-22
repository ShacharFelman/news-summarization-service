"""Serializers for the fetchers app."""
from rest_framework import serializers
from .models import NewsSource, FetchLog


class NewsSourceSerializer(serializers.ModelSerializer):
    """Serializer for NewsSource model."""

    class Meta:
        model = NewsSource
        fields = [
            'id', 'name', 'source_type', 'is_active',
            'config', 'fetch_interval', 'last_fetch',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_fetch', 'created_at', 'updated_at']

    def validate_config(self, value):
        """Validate source configuration."""
        required_fields = ['api_key']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"Missing required field: {field}")
        return value


class FetchLogSerializer(serializers.ModelSerializer):
    """Serializer for FetchLog model."""

    source_name = serializers.CharField(source='source.name', read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = FetchLog
        fields = [
            'id', 'source', 'source_name', 'fetch_type',
            'status', 'started_at', 'completed_at',
            'articles_fetched', 'articles_saved',
            'error_message', 'query_params', 'metadata',
            'duration'
        ]
        read_only_fields = fields

    def get_duration(self, obj):
        """Calculate the duration of the fetch operation."""
        if obj.completed_at and obj.started_at:
            return (obj.completed_at - obj.started_at).total_seconds()
        return None
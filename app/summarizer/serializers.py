from rest_framework import serializers
from .models import Summary

class SummarySerializer(serializers.ModelSerializer):
    """
    Serializer for the Summary model, including support for status values:
    'pending', 'in_progress', 'completed', and 'failed'.
    """
    class Meta:
        model = Summary
        fields = [
            'id', 'ai_model', 'status', 'summary_text', 'word_count', 'tokens_used',
            'created_at', 'completed_at', 'error_message'
        ]
        read_only_fields = fields

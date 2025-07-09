from django.test import TestCase
from django.utils import timezone
from fetchers.serializers import FetchLogSerializer
from fetchers.models import FetchLog


class FetchLogSerializerTest(TestCase):
    def setUp(self):
        self.fetch_log = FetchLog.objects.create(
            source="TestSource",
            status=FetchLog.Status.SUCCESS,
            articles_fetched=10,
            articles_saved=8,
            query_params={'category': 'technology'},
            metadata={'test': 'data'}
        )

    def test_fetch_log_serializer_fields(self):
        """Test that all expected fields are present in the serializer."""
        serializer = FetchLogSerializer(self.fetch_log)
        expected_fields = {
            'id', 'source', 'source_name', 'status', 'started_at', 'completed_at',
            'articles_fetched', 'articles_saved', 'error_message', 'query_params',
            'metadata', 'raw_data_file', 'duration'
        }
        self.assertEqual(set(serializer.data.keys()), expected_fields)

    def test_duration_calculation_with_completion(self):
        """Test duration calculation when fetch is completed."""
        # Set completed_at to 5 seconds after started_at
        self.fetch_log.completed_at = self.fetch_log.started_at + timezone.timedelta(seconds=5)
        self.fetch_log.save()
        
        serializer = FetchLogSerializer(self.fetch_log)
        self.assertEqual(serializer.data['duration'], 5.0)

    def test_duration_calculation_without_completion(self):
        """Test duration calculation when fetch is not completed."""
        self.fetch_log.completed_at = None
        self.fetch_log.save()
        
        serializer = FetchLogSerializer(self.fetch_log)
        self.assertIsNone(serializer.data['duration'])

    def test_source_name_field(self):
        """Test that source_name field is correctly handled."""
        serializer = FetchLogSerializer(self.fetch_log)
        # Since source is a CharField, source_name should be the same as source
        self.assertEqual(serializer.data['source_name'], self.fetch_log.source)

    def test_read_only_fields(self):
        """Test that all fields are read-only as expected."""
        serializer = FetchLogSerializer(self.fetch_log)
        # All fields should be read-only
        self.assertEqual(len(serializer.fields), len(serializer.Meta.read_only_fields))

    def test_json_fields_serialization(self):
        """Test that JSON fields are properly serialized."""
        self.fetch_log.query_params = {'category': 'technology', 'language': 'en'}
        self.fetch_log.metadata = {'fetcher_class': 'NewsApiFetcher', 'version': '1.0'}
        self.fetch_log.save()
        
        serializer = FetchLogSerializer(self.fetch_log)
        self.assertEqual(serializer.data['query_params'], {'category': 'technology', 'language': 'en'})
        self.assertEqual(serializer.data['metadata'], {'fetcher_class': 'NewsApiFetcher', 'version': '1.0'}) 
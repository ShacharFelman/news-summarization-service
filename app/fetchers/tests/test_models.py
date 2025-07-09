from django.test import TestCase
from django.utils import timezone
from fetchers.models import FetchLog


class FetchLogModelTest(TestCase):
    def setUp(self):
        self.fetch_log = FetchLog.objects.create(
            source="TestSource",
            status=FetchLog.Status.PENDING,
            articles_fetched=10,
            articles_saved=8,
            query_params={'category': 'technology'},
            metadata={'test': 'data'}
        )

    def test_str_representation(self):
        expected = f"{self.fetch_log.source} - {self.fetch_log.status} - {self.fetch_log.started_at}"
        self.assertEqual(str(self.fetch_log), expected)

    def test_status_choices(self):
        """Test that status field accepts valid choices."""
        valid_statuses = [choice[0] for choice in FetchLog.Status.choices]
        self.assertIn('PENDING', valid_statuses)
        self.assertIn('IN_PROGRESS', valid_statuses)
        self.assertIn('SUCCESS', valid_statuses)
        self.assertIn('ERROR', valid_statuses)

    def test_complete_method_success(self):
        """Test the complete method with success status."""
        self.fetch_log.complete(
            FetchLog.Status.SUCCESS,
            articles_fetched=15,
            articles_saved=12,
            error_message=""
        )
        self.fetch_log.refresh_from_db()
        
        self.assertEqual(self.fetch_log.status, FetchLog.Status.SUCCESS)
        self.assertIsNotNone(self.fetch_log.completed_at)
        self.assertEqual(self.fetch_log.articles_fetched, 15)
        self.assertEqual(self.fetch_log.articles_saved, 12)
        self.assertEqual(self.fetch_log.error_message, "")

    def test_complete_method_error(self):
        """Test the complete method with error status."""
        error_msg = "API connection failed"
        self.fetch_log.complete(
            FetchLog.Status.ERROR,
            articles_fetched=0,
            articles_saved=0,
            error_message=error_msg
        )
        self.fetch_log.refresh_from_db()
        
        self.assertEqual(self.fetch_log.status, FetchLog.Status.ERROR)
        self.assertIsNotNone(self.fetch_log.completed_at)
        self.assertEqual(self.fetch_log.articles_fetched, 0)
        self.assertEqual(self.fetch_log.articles_saved, 0)
        self.assertEqual(self.fetch_log.error_message, error_msg)

    def test_ordering(self):
        """Test that FetchLog objects are ordered by started_at descending."""
        # Create another fetch log with a later time
        later_log = FetchLog.objects.create(
            source="LaterSource",
            status=FetchLog.Status.SUCCESS
        )
        
        logs = FetchLog.objects.all()
        self.assertEqual(logs[0], later_log)  # Most recent first
        self.assertEqual(logs[1], self.fetch_log)

    def test_default_values(self):
        """Test default values for new FetchLog instances."""
        new_log = FetchLog.objects.create(source="NewSource")
        
        self.assertEqual(new_log.status, FetchLog.Status.PENDING)
        self.assertEqual(new_log.articles_fetched, 0)
        self.assertEqual(new_log.articles_saved, 0)
        self.assertEqual(new_log.query_params, {})
        self.assertEqual(new_log.metadata, {})
        self.assertIsNotNone(new_log.started_at)
        self.assertIsNone(new_log.completed_at)
        self.assertEqual(new_log.error_message, "")
        self.assertEqual(new_log.raw_data_file, "") 
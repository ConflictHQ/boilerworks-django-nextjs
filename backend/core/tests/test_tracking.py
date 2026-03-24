"""
Tests for the Tracking abstract model.

Uses Link (the simplest concrete Tracking subclass) to verify:
- version auto-increments on every save
- simple_history creates a record per save
- created_at / updated_at are populated correctly
"""
from core.models.common import Link
from django.test import TestCase


class TrackingVersionTest(TestCase):

    def test_version_starts_at_one_after_first_save(self):
        link = Link.objects.create(url="https://example.com")
        self.assertEqual(link.version, 1)

    def test_version_increments_on_each_subsequent_save(self):
        link = Link.objects.create(url="https://example.com")
        link.title = "First update"
        link.save()
        link.refresh_from_db()
        self.assertEqual(link.version, 2)

        link.title = "Second update"
        link.save()
        link.refresh_from_db()
        self.assertEqual(link.version, 3)

    def test_created_at_is_set_on_creation(self):
        link = Link.objects.create(url="https://example.com")
        self.assertIsNotNone(link.created_at)

    def test_updated_at_advances_after_save(self):
        link = Link.objects.create(url="https://example.com")
        first_updated_at = link.updated_at
        link.title = "Updated"
        link.save()
        link.refresh_from_db()
        self.assertGreaterEqual(link.updated_at, first_updated_at)


class TrackingHistoryTest(TestCase):

    def test_one_history_record_created_on_save(self):
        link = Link.objects.create(url="https://example.com")
        self.assertEqual(link.history.count(), 1)

    def test_history_record_added_on_each_update(self):
        link = Link.objects.create(url="https://example.com")
        link.title = "v2"
        link.save()
        link.title = "v3"
        link.save()
        self.assertEqual(link.history.count(), 3)

    def test_history_preserves_previous_field_values(self):
        link = Link.objects.create(url="https://example.com", title="original")
        link.title = "updated"
        link.save()

        # Most recent history record first (ordering is by -history_date)
        oldest = link.history.last()
        self.assertEqual(oldest.title, "original")

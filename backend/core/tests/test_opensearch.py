"""
Tests for OpenSearch signal wiring.

Creating a User auto-creates a Profile via post_save → Profile.add_profile.
These tests verify that saving or deleting a Profile triggers the correct
ProfileDocument class method — without needing a live OpenSearch instance.
"""
from unittest.mock import patch

from core.models.user import Profile
from django.contrib.auth.models import User
from django.test import TestCase


class ProfileIndexSignalsTest(TestCase):
    """Post-save and post-delete signals drive ProfileDocument indexing."""

    def setUp(self):
        # User creation triggers Profile.add_profile (post_save on User),
        # which auto-creates a Profile. Retrieve it for use in tests.
        self.user = User.objects.create_user(
            username='opensearch_test',
            email='opensearch@test.com',
        )
        self.profile = Profile.objects.get(user=self.user)

    @patch('core.documents.ProfileDocument.index_profile')
    def test_profile_save_triggers_indexing(self, mock_index):
        self.profile.first_name = 'Updated'
        self.profile.save()
        mock_index.assert_called_once_with(self.profile)

    @patch('core.documents.ProfileDocument.index_profile')
    def test_new_user_creation_indexes_auto_created_profile(self, mock_index):
        # Creating a user auto-creates a profile, which must be indexed.
        new_user = User.objects.create_user(
            username='another_opensearch_user',
            email='another@test.com',
        )
        new_profile = Profile.objects.get(user=new_user)
        mock_index.assert_called_once_with(new_profile)

    @patch('core.documents.ProfileDocument.index_profile')
    @patch('core.documents.ProfileDocument.delete_profile')
    def test_profile_delete_removes_from_index(self, mock_delete, mock_index):
        gid = self.profile.gid
        self.profile.delete()
        mock_delete.assert_called_once_with(gid)

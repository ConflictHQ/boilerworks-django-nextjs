"""Extended dataloader tests — remaining sync batch loaders."""
from django.contrib.auth import get_user_model
from django.test import TestCase

from core.schema.dataloaders import (
    batch_load_profiles_by_gid_sync,
    batch_load_uploads_sync,
)

User = get_user_model()


class BatchLoadProfilesByGidTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='gid_u1', email='gid1@test.com')
        from core.models import Profile
        self.profile = Profile.objects.get(user=self.user)

    def test_loads_by_gid(self):
        # Profile.gid is a UUID primary key — must pass UUID objects, not strings
        from uuid import UUID
        gid = self.profile.gid  # UUID object
        results = batch_load_profiles_by_gid_sync([gid])
        self.assertEqual(len(results), 1)
        self.assertIsNotNone(results[0])
        self.assertEqual(results[0].user_id, self.user.id)

    def test_returns_none_for_missing_gid(self):
        results = batch_load_profiles_by_gid_sync(['00000000-0000-0000-0000-000000000000'])
        self.assertIsNone(results[0])

    def test_empty_keys(self):
        self.assertEqual(batch_load_profiles_by_gid_sync([]), [])


class BatchLoadUploadsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='upload_u1', email='up1@test.com')
        from core.models import Upload
        self.upload = Upload.objects.create(
            name='test_file.png', content_type='image/png',
            created_by=self.user, updated_by=self.user,
        )

    def test_loads_by_id(self):
        results = batch_load_uploads_sync([self.upload.id])
        self.assertEqual(results[0].name, 'test_file.png')

    def test_returns_none_for_missing(self):
        results = batch_load_uploads_sync([99999])
        self.assertIsNone(results[0])

    def test_empty_keys_returns_empty(self):
        results = batch_load_uploads_sync([])
        self.assertEqual(results, [])

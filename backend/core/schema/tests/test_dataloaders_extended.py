"""Extended dataloader tests — batch-contract coverage for the sync loaders.

These loaders back async GraphQL fields (ProfileType.avatar, member
resolution), which schema.execute_sync() cannot drive — the sync batch
functions are the testable unit. The former trivial empty-keys tests were
dropped (#69); only the meaningful batch contracts remain: positional
results and None for missing keys.
"""
from core.schema.dataloaders import batch_load_profiles_by_gid_sync, batch_load_uploads_sync
from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class BatchLoadProfilesByGidTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='gid_u1', email='gid1@test.com')
        from core.models import Profile
        self.profile = Profile.objects.get(user=self.user)

    def test_loads_by_gid_and_preserves_key_order(self):
        # Profile.gid is a UUID primary key — must pass UUID objects, not strings
        from uuid import UUID
        missing = UUID('00000000-0000-0000-0000-000000000000')
        results = batch_load_profiles_by_gid_sync([missing, self.profile.gid])
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0])
        self.assertEqual(results[1].user_id, self.user.id)


class BatchLoadUploadsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='upload_u1', email='up1@test.com')
        from core.models import Upload
        self.upload = Upload.objects.create(
            name='test_file.png', content_type='image/png',
            created_by=self.user, updated_by=self.user,
        )

    def test_loads_by_id_and_preserves_key_order(self):
        results = batch_load_uploads_sync([99999, self.upload.id])
        self.assertEqual(len(results), 2)
        self.assertIsNone(results[0])
        self.assertEqual(results[1].name, 'test_file.png')

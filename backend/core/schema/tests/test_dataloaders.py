from unittest.mock import MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase

from core.schema.context import StrawberryContext
from core.schema.dataloaders import (
    batch_load_first_names_sync,
    batch_load_last_names_sync,
    batch_load_profiles_by_user_id_sync,
    batch_load_users_sync,
)

User = get_user_model()


class BatchLoadUsersTest(TestCase):
    """Tests for the batch_load_users dataloader."""

    def setUp(self):
        self.user1 = User.objects.create_user(username='loader_u1', email='u1@test.com')
        self.user2 = User.objects.create_user(username='loader_u2', email='u2@test.com')

    def test_loads_users_by_id(self):
        results = batch_load_users_sync([self.user1.id, self.user2.id])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].id, self.user1.id)
        self.assertEqual(results[0].username, 'loader_u1')
        self.assertEqual(results[1].id, self.user2.id)
        self.assertEqual(results[1].username, 'loader_u2')

    def test_returns_none_for_missing_ids(self):
        results = batch_load_users_sync([self.user1.id, 99999])
        self.assertEqual(results[0].id, self.user1.id)
        self.assertIsNone(results[1])

    def test_preserves_key_order(self):
        results = batch_load_users_sync([self.user2.id, self.user1.id])
        self.assertEqual(results[0].id, self.user2.id)
        self.assertEqual(results[1].id, self.user1.id)

    def test_empty_keys(self):
        results = batch_load_users_sync([])
        self.assertEqual(results, [])


class BatchLoadProfilesByUserIdTest(TestCase):
    """Tests for the batch_load_profiles_by_user_id dataloader."""

    def setUp(self):
        from organization.models import Organization
        self.org = Organization.objects.create(name='TestOrg')
        self.user1 = User.objects.create_user(
            username='prof_u1', email='prof1@test.com',
            first_name='Alice', last_name='Smith',
        )
        self.user2 = User.objects.create_user(
            username='prof_u2', email='prof2@test.com',
            first_name='Bob', last_name='Jones',
        )

    def test_loads_profiles_by_user_id(self):
        results = batch_load_profiles_by_user_id_sync([self.user1.id, self.user2.id])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].user_id, self.user1.id)
        self.assertEqual(results[1].user_id, self.user2.id)

    def test_returns_none_for_missing_user_id(self):
        results = batch_load_profiles_by_user_id_sync([self.user1.id, 99999])
        self.assertEqual(results[0].user_id, self.user1.id)
        self.assertIsNone(results[1])


class BatchLoadNamesTest(TestCase):
    """Tests for first/last name batch loaders."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='name_u1', email='name1@test.com',
            first_name='AuthFirst', last_name='AuthLast',
        )
        from core.models import Profile
        self.profile1 = Profile.objects.get(user=self.user1)
        self.profile1.first_name = 'ProfileFirst'
        self.profile1.last_name = 'ProfileLast'
        self.profile1.save()

    def test_first_name_prefers_profile(self):
        results = batch_load_first_names_sync([self.user1.id])
        self.assertEqual(results[0], 'ProfileFirst')

    def test_last_name_prefers_profile(self):
        results = batch_load_last_names_sync([self.user1.id])
        self.assertEqual(results[0], 'ProfileLast')

    def test_falls_back_to_user_name_when_profile_empty(self):
        self.profile1.first_name = ''
        self.profile1.save()
        results = batch_load_first_names_sync([self.user1.id])
        self.assertEqual(results[0], 'AuthFirst')

    def test_returns_empty_string_for_missing_user(self):
        results = batch_load_first_names_sync([99999])
        self.assertEqual(results[0], '')


class StrawberryContextTest(TestCase):
    """Tests for StrawberryContext."""

    def test_cached_user_property(self):
        mock_request = MagicMock()
        mock_request.user = User.objects.create_user(username='ctx_user', email='ctx@test.com')
        ctx = StrawberryContext(mock_request)
        self.assertEqual(ctx.user.username, 'ctx_user')
        self.assertIs(ctx.user, ctx.user)

    def test_permission_caching(self):
        ctx = StrawberryContext(MagicMock())
        call_count = 0

        def check():
            nonlocal call_count
            call_count += 1
            return True

        result1 = ctx.check_permission('some_perm', check)
        result2 = ctx.check_permission('some_perm', check)
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertEqual(call_count, 1, "Permission callback should only be called once")

    def test_get_loader_returns_same_instance(self):
        ctx = StrawberryContext(MagicMock())

        async def batch_fn(keys):
            return keys

        loader1 = ctx.get_loader('test', batch_fn)
        loader2 = ctx.get_loader('test', batch_fn)
        self.assertIs(loader1, loader2, "Same name should return same DataLoader instance")

    def test_get_loader_different_names_different_instances(self):
        ctx = StrawberryContext(MagicMock())

        async def batch_fn(keys):
            return keys

        loader1 = ctx.get_loader('a', batch_fn)
        loader2 = ctx.get_loader('b', batch_fn)
        self.assertIsNot(loader1, loader2)

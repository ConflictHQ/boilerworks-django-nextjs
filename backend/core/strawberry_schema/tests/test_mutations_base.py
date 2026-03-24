from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from graphql import GraphQLError

from core.strawberry_schema.common import GlobalIDUtils
from core.strawberry_schema.mutations.base import (
    resolve_instance_from_id,
    restricted_serializer_mutate,
)

User = get_user_model()


class RestrictedSerializerMutateTest(TestCase):
    """Tests for the restricted_serializer_mutate helper."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='mut_test', email='mut@test.com', password='testpass',
        )
        self.mock_info = MagicMock()
        self.mock_info.context.user = self.user
        self.mock_info.context.request = MagicMock()

    def test_calls_add_permission_when_no_instance(self):
        mock_model = MagicMock()
        mock_serializer_cls = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_cls.return_value = mock_serializer

        result = restricted_serializer_mutate(
            mock_serializer_cls, mock_model, self.mock_info, data={}, instance=None,
        )

        mock_model.p('model').add.check.assert_called_once_with(self.user)
        self.assertTrue(result.ok)

    def test_calls_change_permission_when_instance_provided(self):
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_serializer_cls = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_cls.return_value = mock_serializer

        result = restricted_serializer_mutate(
            mock_serializer_cls, mock_model, self.mock_info,
            data={}, instance=mock_instance,
        )

        mock_model.p('model').change.check.assert_called_once_with(self.user)
        self.assertTrue(result.ok)

    def test_returns_errors_on_validation_failure(self):
        mock_model = MagicMock()
        mock_serializer_cls = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'name': ['This field is required.']}
        mock_serializer_cls.return_value = mock_serializer

        result = restricted_serializer_mutate(
            mock_serializer_cls, mock_model, self.mock_info, data={},
        )

        self.assertFalse(result.ok)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0].field, 'name')

    def test_passes_instance_to_serializer(self):
        mock_model = MagicMock()
        mock_instance = MagicMock()
        mock_serializer_cls = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer_cls.return_value = mock_serializer

        restricted_serializer_mutate(
            mock_serializer_cls, mock_model, self.mock_info,
            data={'field': 'value'}, instance=mock_instance,
        )

        call_kwargs = mock_serializer_cls.call_args[1]
        self.assertEqual(call_kwargs['instance'], mock_instance)
        self.assertTrue(call_kwargs['partial'])


class ResolveInstanceFromIdTest(TestCase):
    """Tests for the resolve_instance_from_id helper."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='resolve_test', email='resolve@test.com', password='testpass',
        )

    def test_resolves_by_raw_pk(self):
        instance = resolve_instance_from_id(User, str(self.user.pk))
        self.assertEqual(instance.pk, self.user.pk)

    def test_resolves_by_global_id(self):
        global_id = GlobalIDUtils.to_global_id('UserType', self.user.pk)
        instance = resolve_instance_from_id(User, global_id, type_name='UserType')
        self.assertEqual(instance.pk, self.user.pk)

    def test_raises_for_nonexistent_id(self):
        with self.assertRaises(GraphQLError) as ctx:
            resolve_instance_from_id(User, '99999')
        self.assertIn('not found', str(ctx.exception))

    def test_raises_for_empty_id(self):
        with self.assertRaises(GraphQLError):
            resolve_instance_from_id(User, '')


class FindObjectByGlobalIdTest(TestCase):
    """Tests for GlobalIDUtils.find_object_by_global_id."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='find_test', email='find@test.com', password='testpass',
        )

    def test_finds_user_by_global_id(self):
        global_id = GlobalIDUtils.to_global_id('User', self.user.pk)
        found = GlobalIDUtils.find_object_by_global_id(global_id)
        self.assertEqual(found.pk, self.user.pk)

    def test_returns_none_for_missing_when_not_raising(self):
        global_id = GlobalIDUtils.to_global_id('User', 99999)
        found = GlobalIDUtils.find_object_by_global_id(global_id, raise_not_found=False)
        self.assertIsNone(found)

    def test_raises_for_missing_when_raising(self):
        global_id = GlobalIDUtils.to_global_id('User', 99999)
        with self.assertRaises(GraphQLError):
            GlobalIDUtils.find_object_by_global_id(global_id)

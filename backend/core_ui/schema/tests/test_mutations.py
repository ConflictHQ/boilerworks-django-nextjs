"""Integration tests for core_ui GraphQL mutations.

Tests component create, update, and permission-denied paths via
schema.execute_sync() with StrawberryContext.
"""
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from config.permissions import FieldPermissions
from config.schema import schema
from core.schema.context import StrawberryContext
from core_ui.models import Component

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


def _build_mock_field_permissions(*, allow=True):
    """Build a mock FieldPermissions whose add/change/delete/view .check() either passes or raises."""
    fp = MagicMock()
    for attr in ('add', 'change', 'delete', 'view'):
        perm_mock = MagicMock()
        if allow:
            perm_mock.check.return_value = True
        else:
            perm_mock.check.side_effect = PermissionDenied('User does not have required permissions')
        setattr(fp, attr, perm_mock)
    return fp


def _build_permissions_map(*, allow=True):
    """Build a dict-like permissions map that returns real FieldPermissions for unknown fields.

    The 'model' key gets a mock with working check() methods.
    All other keys get a real FieldPermissions(name) with None add/change/delete/view,
    which the FieldRestrictedSerializer treats as 'no permission configured, allow by default'.
    """
    model_fp = _build_mock_field_permissions(allow=allow)
    store = {'model': model_fp}

    class PermissionsMap(dict):
        def __getitem__(self, key):
            if key in store:
                return store[key]
            # Mirror ModelPermissions.__getitem__: unknown fields get a bare FieldPermissions
            return FieldPermissions(key)

        def __contains__(self, key):
            return True  # Prevent KeyError from defaulting in p()

    return PermissionsMap(store)


class ComponentMutationTest(TestCase):
    """Tests for the component create/update mutation."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='MutTestOrg')
        self.superuser = User.objects.create_superuser(
            username='comp_mut_super', email='comp_mut@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.superuser, is_active=True,
        )
        self.superuser.profile.active_organization = self.org
        self.superuser.profile.save()

        self.context = StrawberryContext(FakeRequest(self.superuser))

        # Patch model_permissions to return our custom permissions map
        self._perm_patcher = patch.object(
            Component, 'model_permissions',
            return_value=_build_permissions_map(allow=True),
        )
        self._perm_patcher.start()

    def tearDown(self):
        self._perm_patcher.stop()

    def test_component_create(self):
        """Create a component via mutation and verify it exists in the DB."""
        mutation = """
            mutation {
                component(input: {
                    name: "Dashboard"
                    slug: "dashboard"
                    description: "Main dashboard"
                    isActive: true
                    path: "/dashboard"
                    icon: "icon-dashboard"
                }) {
                    ok
                    errors { field messages }
                    id
                }
            }
        """
        result = schema.execute_sync(mutation, context_value=self.context)

        self.assertIsNone(result.errors)
        data = result.data['component']
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], [])
        self.assertIsNotNone(data['id'])

        # Verify in the database
        comp = Component.objects.get(slug='dashboard')
        self.assertEqual(comp.name, 'Dashboard')
        self.assertEqual(comp.description, 'Main dashboard')
        self.assertTrue(comp.is_active)
        self.assertEqual(comp.path, '/dashboard')
        self.assertEqual(comp.icon, 'icon-dashboard')
        self.assertEqual(comp.created_by_id, self.superuser.id)
        self.assertEqual(comp.updated_by_id, self.superuser.id)

    def test_component_update(self):
        """Create a component, then update it via mutation, and verify changes."""
        comp = Component.objects.create(
            name='Old Name',
            slug='updatable',
            description='Old description',
            is_active=True,
            path='/old',
            icon='icon-old',
            created_by=self.superuser,
            updated_by=self.superuser,
        )

        mutation = """
            mutation($id: ID!) {
                component(input: {
                    id: $id
                    name: "New Name"
                    description: "New description"
                    path: "/new"
                    icon: "icon-new"
                }) {
                    ok
                    errors { field messages }
                    id
                }
            }
        """
        result = schema.execute_sync(
            mutation,
            context_value=self.context,
            variable_values={'id': str(comp.pk)},
        )

        self.assertIsNone(result.errors)
        data = result.data['component']
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], [])

        # Verify the database was updated
        comp.refresh_from_db()
        self.assertEqual(comp.name, 'New Name')
        self.assertEqual(comp.description, 'New description')
        self.assertEqual(comp.path, '/new')
        self.assertEqual(comp.icon, 'icon-new')
        # Slug should remain unchanged since we did not pass it
        self.assertEqual(comp.slug, 'updatable')

    def test_component_create_permission_denied(self):
        """A non-superuser without permissions should be denied component creation."""
        from organization.models import OrganizationMember

        # Stop the allow-all patch so we can install a deny patch
        self._perm_patcher.stop()

        regular_user = User.objects.create_user(
            username='comp_regular', email='comp_reg@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=regular_user, is_active=True,
        )
        regular_user.profile.active_organization = self.org
        regular_user.profile.save()

        ctx = StrawberryContext(FakeRequest(regular_user))

        # Patch permissions to deny access
        with patch.object(
            Component, 'model_permissions',
            return_value=_build_permissions_map(allow=False),
        ):
            mutation = """
                mutation {
                    component(input: {
                        name: "Forbidden"
                        slug: "forbidden"
                    }) {
                        ok
                        errors { field messages }
                        id
                    }
                }
            """
            result = schema.execute_sync(mutation, context_value=ctx)

        # Re-start the allow patch for tearDown
        self._perm_patcher.start()

        # Permission denied surfaces as a GraphQL error
        self.assertIsNotNone(result.errors)
        self.assertGreater(len(result.errors), 0)

        error_messages = ' '.join(str(e) for e in result.errors)
        self.assertTrue(
            'permission' in error_messages.lower() or 'denied' in error_messages.lower(),
            f'Expected permission/denied error, got: {error_messages}',
        )

        # Verify the component was NOT created
        self.assertFalse(Component.objects.filter(slug='forbidden').exists())

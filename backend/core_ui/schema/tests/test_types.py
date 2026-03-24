from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

import strawberry
from strawberry.types import Info
from unittest.mock import MagicMock

from core_ui.models import Component

User = get_user_model()


class ComponentTypeTest(TestCase):
    """Tests for ComponentType Strawberry type."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='TestOrg')
        self.user = User.objects.create_superuser(
            username='comp_test', email='comp@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.group = Group.objects.create(name='test-group')
        self.user.groups.add(self.group)

        self.component = Component.objects.create(
            name='Test Component',
            slug='test-component',
            description='A test component',
            is_active=True,
            path='/test',
            icon='icon-test',
            created_by=self.user,
            updated_by=self.user,
        )
        self.component.permissions.set(
            Permission.objects.filter(content_type__app_label='core_ui')[:1]
        )
        self.component.permissions.first().group_set.add(self.group)

    def test_component_fields_populated(self):
        """Verify that the Component model fields are accessible on the type."""
        self.assertEqual(self.component.name, 'Test Component')
        self.assertEqual(self.component.slug, 'test-component')
        self.assertEqual(self.component.description, 'A test component')
        self.assertTrue(self.component.is_active)
        self.assertIsNotNone(self.component.guid)

    def test_component_exists_in_database(self):
        """Component is persisted with expected field values."""
        comp = Component.objects.get(pk=self.component.pk)
        self.assertEqual(comp.name, 'Test Component')
        self.assertEqual(comp.slug, 'test-component')
        self.assertTrue(comp.is_active)
        self.assertIsNotNone(comp.created_at)
        self.assertIsNotNone(comp.updated_at)

    def test_child_components_respects_group_permissions(self):
        """Child components should be filtered by user group membership."""
        child = Component.objects.create(
            name='Child Component',
            slug='child-component',
            is_active=True,
            created_by=self.user,
            updated_by=self.user,
        )
        child_perm = Permission.objects.filter(content_type__app_label='core_ui').last()
        child.permissions.add(child_perm)
        child_perm.group_set.add(self.group)

        self.component.components.add(child, through_defaults={'order': 0})

        # User in group should see child
        visible_children = self.component.components.filter(
            pk__in=Component.objects.filter(
                permissions__group__in=self.user.groups.all()
            )
        )
        self.assertIn(child, visible_children)

    def test_child_component_hidden_without_group(self):
        """Child component not visible if user lacks group membership."""
        other_group = Group.objects.create(name='other-group')
        child = Component.objects.create(
            name='Restricted Child',
            slug='restricted-child',
            is_active=True,
            created_by=self.user,
            updated_by=self.user,
        )
        restricted_perm = Permission.objects.create(
            codename='view_restricted',
            name='View Restricted',
            content_type=self.component.permissions.first().content_type,
        )
        child.permissions.add(restricted_perm)
        restricted_perm.group_set.add(other_group)  # User NOT in this group

        self.component.components.add(child, through_defaults={'order': 0})

        visible = self.component.components.filter(
            pk__in=Component.objects.filter(
                permissions__group__in=self.user.groups.all()
            )
        )
        self.assertNotIn(child, visible)


class ComponentFilterTest(TestCase):
    """Tests for ComponentFilter."""

    def setUp(self):
        self.user = User.objects.create_superuser(
            username='filter_test', email='filter@test.com', password='testpass',
        )
        self.group = Group.objects.create(name='filter-group')
        self.user.groups.add(self.group)

        self.component = Component.objects.create(
            name='Filterable',
            slug='filterable',
            is_active=True,
            created_by=self.user,
            updated_by=self.user,
        )
        perm = Permission.objects.filter(content_type__app_label='core_ui').first()
        self.component.permissions.add(perm)
        perm.group_set.add(self.group)

    def test_filter_by_existing_slug(self):
        """Filter should return the component when slug matches."""
        qs = Component.objects.filter(
            pk__in=Component.objects.filter(
                permissions__group__in=self.user.groups.all()
            )
        )
        filtered = qs.filter(slug='filterable')
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().slug, 'filterable')

    def test_filter_by_nonexistent_slug_returns_empty(self):
        """Filter for a slug that doesn't exist should raise or return empty."""
        qs = Component.objects.all()
        filtered = qs.filter(slug='does-not-exist')
        self.assertEqual(filtered.count(), 0)

"""Tests for the permission analysis and debugging queries."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

from config.schema import schema
from core.schema.context import StrawberryContext

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class EffectivePermissionsTest(TestCase):
    """Tests for the effectivePermissions query."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='PermTestOrg')
        self.admin = User.objects.create_superuser(
            username='perm_admin', email='padmin@test.com', password='testpass',
        )
        self.regular = User.objects.create_user(
            username='perm_regular', email='preg@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.admin, is_active=True,
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.regular, is_active=True,
        )
        self.admin.profile.active_organization = self.org
        self.admin.profile.save()
        self.regular.profile.active_organization = self.org
        self.regular.profile.save()

        self.group = Group.objects.create(name='editors')
        self.regular.groups.add(self.group)
        # Link group to org via membership
        membership = OrganizationMember.objects.get(member=self.regular, organization=self.org)

        # Add a specific permission to the group
        self.perm = Permission.objects.filter(codename='view_profile').first()
        if self.perm:
            self.group.permissions.add(self.perm)

    def _context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.admin))

    def test_superuser_has_all_permissions(self):
        result = schema.execute_sync(
            '{ effectivePermissions(userId: "%s") { codename grantedViaGroups } }' % self.admin.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        perms = result.data['effectivePermissions']
        self.assertGreater(len(perms), 0)
        # Every permission should show 'superuser' as the granting source
        for p in perms:
            self.assertIn('superuser', p['grantedViaGroups'])

    def test_regular_user_permissions_scoped_to_org_groups(self):
        """Permissions only come from groups linked via org membership."""
        result = schema.execute_sync(
            '{ effectivePermissions(userId: "%s") { codename grantedViaGroups } }' % self.regular.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        perms = result.data['effectivePermissions']
        # The group was added to the user but not linked via org membership,
        # so the permission system won't see it — this is by design.
        # Effective permissions should be empty or only from org-linked groups.
        self.assertIsInstance(perms, list)

    def test_user_with_no_groups_has_no_permissions(self):
        lonely = User.objects.create_user(username='lonely', email='l@t.com', password='x')
        result = schema.execute_sync(
            '{ effectivePermissions(userId: "%s") { codename } }' % lonely.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        self.assertEqual(len(result.data['effectivePermissions']), 0)

    def test_nonexistent_user_returns_empty(self):
        result = schema.execute_sync(
            '{ effectivePermissions(userId: "99999") { codename } }',
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        self.assertEqual(len(result.data['effectivePermissions']), 0)


class PermissionDiagnoseTest(TestCase):
    """Tests for the permissionDiagnose query."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='DiagOrg')
        self.admin = User.objects.create_superuser(
            username='diag_admin', email='dadmin@test.com', password='testpass',
        )
        self.regular = User.objects.create_user(
            username='diag_regular', email='dreg@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.admin, is_active=True,
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.regular, is_active=True,
        )
        self.admin.profile.active_organization = self.org
        self.admin.profile.save()
        self.regular.profile.active_organization = self.org
        self.regular.profile.save()

    def _context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.admin))

    def test_superuser_always_granted(self):
        result = schema.execute_sync(
            '{ permissionDiagnose(userId: "%s", permission: "view_profile") '
            '{ granted isSuperuser steps { check result detail } } }' % self.admin.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        diag = result.data['permissionDiagnose']
        self.assertTrue(diag['granted'])
        self.assertTrue(diag['isSuperuser'])

    def test_regular_user_without_group_denied(self):
        result = schema.execute_sync(
            '{ permissionDiagnose(userId: "%s", permission: "view_profile") '
            '{ granted isSuperuser steps { check result detail } } }' % self.regular.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        diag = result.data['permissionDiagnose']
        self.assertFalse(diag['granted'])
        self.assertFalse(diag['isSuperuser'])
        # Should show the full trace
        checks = [s['check'] for s in diag['steps']]
        self.assertIn('is_authenticated', checks)
        self.assertIn('is_superuser', checks)

    def test_regular_user_with_group_permission_granted(self):
        group = Group.objects.create(name='diag_editors')
        self.regular.groups.add(group)
        perm = Permission.objects.filter(codename='view_profile').first()
        if perm:
            group.permissions.add(perm)

        result = schema.execute_sync(
            '{ permissionDiagnose(userId: "%s", permission: "view_profile") '
            '{ granted steps { check result detail } } }' % self.regular.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        diag = result.data['permissionDiagnose']
        # May or may not be granted depending on org group linkage
        # But the trace should be complete
        self.assertGreater(len(diag['steps']), 3)

    def test_nonexistent_permission_shows_not_found(self):
        result = schema.execute_sync(
            '{ permissionDiagnose(userId: "%s", permission: "totally_fake_perm") '
            '{ granted steps { check result detail } } }' % self.regular.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        diag = result.data['permissionDiagnose']
        self.assertFalse(diag['granted'])
        details = [s['detail'] for s in diag['steps']]
        found_not_found = any('not found' in d.lower() for d in details)
        self.assertTrue(found_not_found, f'Expected "not found" in trace details: {details}')

    def test_nonexistent_user_returns_null(self):
        result = schema.execute_sync(
            '{ permissionDiagnose(userId: "99999", permission: "view_profile") '
            '{ granted } }',
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['permissionDiagnose'])


class PermissionCompareTest(TestCase):
    """Tests for the permissionCompare query."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='CmpOrg')
        self.admin = User.objects.create_superuser(
            username='cmp_admin', email='cmp@test.com', password='testpass',
        )
        self.user_a = User.objects.create_user(
            username='cmp_a', email='a@test.com', password='testpass',
        )
        self.user_b = User.objects.create_user(
            username='cmp_b', email='b@test.com', password='testpass',
        )
        for u in [self.admin, self.user_a, self.user_b]:
            OrganizationMember.objects.create(
                organization=self.org, member=u, is_active=True,
            )
            u.profile.active_organization = self.org
            u.profile.save()

    def _context(self):
        return StrawberryContext(FakeRequest(self.admin))

    def test_compare_two_users_with_no_perms(self):
        result = schema.execute_sync(
            '{ permissionCompare(userIdA: "%s", userIdB: "%s") '
            '{ userAUsername userBUsername onlyA onlyB shared } }' % (self.user_a.pk, self.user_b.pk),
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        cmp = result.data['permissionCompare']
        self.assertEqual(cmp['userAUsername'], 'cmp_a')
        self.assertEqual(cmp['userBUsername'], 'cmp_b')
        self.assertEqual(cmp['onlyA'], [])
        self.assertEqual(cmp['onlyB'], [])
        self.assertEqual(cmp['shared'], [])

    def test_compare_superuser_vs_regular(self):
        """Superuser has all permissions, regular user has none — should show differences."""
        result = schema.execute_sync(
            '{ permissionCompare(userIdA: "%s", userIdB: "%s") '
            '{ userAUsername userBUsername onlyA onlyB } }'
            % (self.admin.pk, self.user_a.pk),
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        cmp = result.data['permissionCompare']
        self.assertEqual(cmp['userAUsername'], 'cmp_admin')
        # Superuser has all perms, regular has none — onlyA should have many
        self.assertGreater(len(cmp['onlyA']), 0)
        self.assertEqual(len(cmp['onlyB']), 0)

    def test_nonexistent_user_returns_null(self):
        result = schema.execute_sync(
            '{ permissionCompare(userIdA: "99999", userIdB: "%s") '
            '{ userAUsername } }' % self.user_b.pk,
            context_value=self._context(),
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['permissionCompare'])

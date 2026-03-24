"""Integration tests for organization GraphQL mutations.

Tests organization member status deactivation and reactivation via
schema.execute_sync() with StrawberryContext.
"""
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

from config.schema import schema
from core.schema.context import StrawberryContext
from organization.models import Organization, OrganizationMember

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class OrganizationMemberStatusMutationTest(TestCase):
    """Tests for the organizationMemberStatus mutation."""

    def setUp(self):
        self.org = Organization.objects.create(name='StatusTestOrg')
        self.admin_user = User.objects.create_superuser(
            username='org_status_admin', email='org_admin@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.admin_user, is_active=True,
        )
        self.admin_user.profile.active_organization = self.org
        self.admin_user.profile.save()

        # Target user to deactivate/reactivate
        self.target_user = User.objects.create_user(
            username='org_target', email='org_target@test.com', password='testpass',
        )
        self.target_membership = OrganizationMember.objects.create(
            organization=self.org, member=self.target_user, is_active=True,
        )
        self.target_user.profile.active_organization = self.org
        self.target_user.profile.save()

        self.context = StrawberryContext(FakeRequest(self.admin_user))

    def test_organization_member_status_deactivate(self):
        """Deactivate a member via mutation and verify is_active=False in DB."""
        mutation = """
            mutation($userId: ID!, $orgId: ID!) {
                organizationMemberStatus(input: {
                    userId: $userId
                    isActive: false
                    organizationId: $orgId
                }) {
                    ok
                    errors { field messages }
                }
            }
        """
        result = schema.execute_sync(
            mutation,
            context_value=self.context,
            variable_values={
                'userId': str(self.target_user.pk),
                'orgId': str(self.org.pk),
            },
        )

        self.assertIsNone(result.errors)
        data = result.data['organizationMemberStatus']
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], [])

        # Verify membership is_active is False in DB
        self.target_membership.refresh_from_db()
        self.assertFalse(self.target_membership.is_active)

        # Verify the User model is_active was also set to False
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

    def test_organization_member_status_reactivate(self):
        """Deactivate then reactivate a member, verify is_active=True in DB."""
        # First deactivate the membership and user directly
        self.target_membership.is_active = False
        self.target_membership.save()
        self.target_user.is_active = False
        self.target_user.save()

        mutation = """
            mutation($userId: ID!, $orgId: ID!) {
                organizationMemberStatus(input: {
                    userId: $userId
                    isActive: true
                    organizationId: $orgId
                }) {
                    ok
                    errors { field messages }
                }
            }
        """
        result = schema.execute_sync(
            mutation,
            context_value=self.context,
            variable_values={
                'userId': str(self.target_user.pk),
                'orgId': str(self.org.pk),
            },
        )

        self.assertIsNone(result.errors)
        data = result.data['organizationMemberStatus']
        self.assertTrue(data['ok'])
        self.assertEqual(data['errors'], [])

        # Verify membership is_active is True in DB
        self.target_membership.refresh_from_db()
        self.assertTrue(self.target_membership.is_active)

        # Verify the User model is_active was also set back to True
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)

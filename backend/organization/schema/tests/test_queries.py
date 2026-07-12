"""Integration tests for organization GraphQL queries (issue #69).

Replaces the model-level OrganizationMemberModelTest: organization identity
(guid/slug, never the integer pk) and membership state are asserted through
the GraphQL layer.
"""
from config.schema import schema
from core.schema.context import StrawberryContext
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from organization.models import Organization, OrganizationMember

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class OrganizationQueryTest(TestCase):
    """Tests for the organizations and members queries."""

    def setUp(self):
        self.org = Organization.objects.create(name='Query Org')
        self.user = User.objects.create_superuser(
            username='org_query_admin', email='org_query@test.com', password='testpass',
        )
        self.membership = OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()
        self.context = StrawberryContext(FakeRequest(self.user))

    def _execute(self, query, variables=None):
        return schema.execute_sync(
            query, variable_values=variables, context_value=self.context,
        )

    def test_organizations_query_exposes_guid_and_slug(self):
        """Organizations resolve with guid/slug identifiers (no integer pk)."""
        result = self._execute('query { organizations { name guid slug } }')
        self.assertIsNone(result.errors)
        orgs = result.data['organizations']
        self.assertEqual(len(orgs), 1)
        self.assertEqual(orgs[0]['name'], 'Query Org')
        self.assertEqual(orgs[0]['guid'], str(self.org.guid))
        self.assertEqual(orgs[0]['slug'], 'query-org')

    def test_organizations_query_search_filter(self):
        """The query argument filters organizations by search terms."""
        Organization.objects.create(name='Other Org')
        result = self._execute(
            'query Search($q: String) { organizations(query: $q) { name } }',
            {'q': 'query'},
        )
        self.assertIsNone(result.errors)
        self.assertEqual(
            [o['name'] for o in result.data['organizations']], ['Query Org'],
        )

    def test_members_query_reflects_membership_state(self):
        """Membership state changes are visible through the members query."""
        query = 'query { members { isActive organization { slug } } }'
        result = self._execute(query)
        self.assertIsNone(result.errors)
        members = result.data['members']
        self.assertEqual(len(members), 1)
        self.assertTrue(members[0]['isActive'])
        self.assertEqual(members[0]['organization']['slug'], 'query-org')

        self.membership.is_active = False
        self.membership.save()
        result = self._execute(query)
        self.assertIsNone(result.errors)
        self.assertFalse(result.data['members'][0]['isActive'])

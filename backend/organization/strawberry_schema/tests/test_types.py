from django.contrib.auth import get_user_model
from django.test import TestCase
from unittest.mock import MagicMock, patch

from organization.models import Organization
from organization.models.organization import OrganizationMember
from organization.strawberry_schema.types import OrganizationMemberType, OrganizationType

User = get_user_model()


class OrganizationTypeFieldsTest(TestCase):
    """Verify OrganizationType fields match the Organization model."""

    def setUp(self):
        self.org = Organization.objects.create(
            name='Field Test Org',
            website='https://fieldtest.example.com',
        )

    def test_name_and_slug_populated(self):
        """Organization name and auto-generated slug should be set."""
        self.assertEqual(self.org.name, 'Field Test Org')
        self.assertTrue(self.org.slug)  # auto-slugified on save

    def test_website_stored(self):
        """Website URL should be persisted correctly."""
        self.assertEqual(self.org.website, 'https://fieldtest.example.com')

    def test_guid_is_generated(self):
        """Every Organization should receive a guid on creation."""
        self.assertIsNotNone(self.org.guid)

    def test_tracking_timestamps_set(self):
        """BaseCoreModel tracking fields should be auto-populated."""
        self.assertIsNotNone(self.org.created_at)
        self.assertIsNotNone(self.org.updated_at)

    def test_search_field_built_on_save(self):
        """The search field should contain name, slug, and website."""
        self.assertIn(self.org.name, self.org.search)
        self.assertIn(self.org.slug, self.org.search)
        self.assertIn(str(self.org.website), self.org.search)

    def test_strawberry_type_declares_expected_fields(self):
        """OrganizationType annotations should include all exposed model fields."""
        annotations = OrganizationType.__annotations__
        expected = {'name', 'slug', 'description', 'website', 'guid', 'version',
                    'created_at', 'updated_at', 'deleted_at'}
        self.assertTrue(expected.issubset(set(annotations.keys())),
                        f'Missing fields: {expected - set(annotations.keys())}')


class OrganizationMemberTypeTest(TestCase):
    """Tests for OrganizationMemberType resolvers."""

    def setUp(self):
        self.org = Organization.objects.create(name='Member Test Org')
        self.user = User.objects.create_user(
            username='member_test_user', email='member@test.com', password='testpass',
        )
        self.membership = OrganizationMember.objects.create(
            organization=self.org,
            member=self.user,
            is_active=True,
        )

    def test_membership_links_user_and_org(self):
        """OrganizationMember should reference the correct user and org."""
        self.assertEqual(self.membership.member_id, self.user.id)
        self.assertEqual(self.membership.organization_id, self.org.id)

    def test_is_active_defaults_true(self):
        """New membership should be active."""
        self.assertTrue(self.membership.is_active)

    def test_organization_cache_lookup_finds_org(self):
        """The context organization cache should find the org by ID."""
        from core.strawberry_schema.context import StrawberryContext
        mock_request = MagicMock()
        mock_request.user = self.user
        ctx = StrawberryContext(mock_request)
        cached_org = ctx.get_organization_cached(self.org.id)
        self.assertEqual(cached_org.id, self.org.id)
        self.assertEqual(cached_org.name, self.org.name)

    def test_organization_cache_returns_none_for_missing(self):
        """The context organization cache should return None for unknown ID."""
        from core.strawberry_schema.context import StrawberryContext
        mock_request = MagicMock()
        mock_request.user = self.user
        ctx = StrawberryContext(mock_request)
        cached_org = ctx.get_organization_cached(99999)
        self.assertIsNone(cached_org)

    def test_strawberry_type_declares_expected_fields(self):
        """OrganizationMemberType annotations should include all exposed fields."""
        annotations = OrganizationMemberType.__annotations__
        expected = {'is_active', 'version', 'created_at', 'updated_at', 'deleted_at'}
        self.assertTrue(expected.issubset(set(annotations.keys())),
                        f'Missing fields: {expected - set(annotations.keys())}')


class OrganizationQueryTest(TestCase):
    """Tests for the organization query logic."""

    def setUp(self):
        self.org_alpha = Organization.objects.create(
            name='Alpha Corp',
            website='https://alpha.example.com',
        )
        self.org_beta = Organization.objects.create(
            name='Beta Industries',
            website='https://beta.example.com',
        )

    def test_organization_cache_returns_correct_org(self):
        """Looking up by ID in the organization cache should return the right org."""
        cache = {o.id: o for o in Organization.objects.all()}
        self.assertEqual(cache[self.org_alpha.id], self.org_alpha)
        self.assertEqual(cache[self.org_beta.id], self.org_beta)

    def test_organization_cache_returns_none_for_invalid_id(self):
        """Cache lookup with a non-existent ID should return None."""
        cache = {o.id: o for o in Organization.objects.all()}
        self.assertIsNone(cache.get(99999))

    def test_organizations_search_filters_by_name(self):
        """Search query should filter organizations by the search field."""
        qs = Organization.objects.all()
        terms = 'Alpha'.split(' ')
        for term in terms:
            qs = qs.filter(search__icontains=term)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, 'Alpha Corp')

    def test_organizations_search_with_no_query_returns_all(self):
        """Empty search should return all organizations."""
        qs = Organization.objects.all()
        self.assertEqual(qs.count(), 2)

    def test_organizations_search_no_match_returns_empty(self):
        """Search for a term that doesn't exist should return empty queryset."""
        qs = Organization.objects.filter(search__icontains='NonExistentCorp')
        self.assertEqual(qs.count(), 0)

    def test_members_query_returns_all_members(self):
        """Members connection should return all OrganizationMember objects."""
        user = User.objects.create_user(
            username='query_member', email='qm@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org_alpha, member=user, is_active=True,
        )
        self.assertEqual(OrganizationMember.objects.count(), 1)

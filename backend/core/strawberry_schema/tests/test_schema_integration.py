"""Integration tests for the assembled Strawberry schema.

Tests that the schema can execute queries and mutations end-to-end,
verifying the full pipeline from GraphQL string → execution → response.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase

from config.strawberry_schema import schema, schema_auth
from core.strawberry_schema.context import StrawberryContext

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = {}
        self.headers = {}


class SchemaIntrospectionTest(TestCase):
    """Tests that the schema can be introspected."""

    def test_schema_generates_sdl(self):
        sdl = schema.as_str()
        self.assertIn('type Query', sdl)
        self.assertIn('type Mutation', sdl)
        self.assertGreater(len(sdl), 1000)

    def test_auth_schema_generates_sdl(self):
        sdl = schema_auth.as_str()
        self.assertIn('type AuthQuery', sdl)
        self.assertIn('type AuthMutation', sdl)

    def test_typename_query(self):
        result = schema.execute_sync('{ __typename }')
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['__typename'], 'Query')

    def test_auth_typename_query(self):
        result = schema_auth.execute_sync('{ __typename }')
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['__typename'], 'AuthQuery')


class SchemaQueryTest(TestCase):
    """Tests for executing queries against the assembled schema."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='IntegrationOrg')
        self.user = User.objects.create_superuser(
            username='schema_test', email='schema@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.context = StrawberryContext(FakeRequest(self.user))

    def test_components_query_returns_list(self):
        result = schema.execute_sync(
            '{ components { name slug } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        self.assertIsInstance(result.data['components'], list)

    def test_component_query_returns_null_for_missing(self):
        result = schema.execute_sync(
            '{ component(slug: "nonexistent") { name } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['component'])

    def test_organizations_query(self):
        result = schema.execute_sync(
            '{ organizations { name } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        orgs = result.data['organizations']
        self.assertIsInstance(orgs, list)
        org_names = [o['name'] for o in orgs]
        self.assertIn('IntegrationOrg', org_names)

    def test_devices_query_returns_list(self):
        result = schema.execute_sync(
            '{ devices { name } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        self.assertIsInstance(result.data['devices'], list)


class SchemaAuthMutationTest(TestCase):
    """Tests for auth mutations."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='auth_mut_test', email='authmut@test.com', password='testpass123',
        )

    def test_login_with_valid_credentials(self):
        from django.test import RequestFactory
        from django.contrib.sessions.backends.db import SessionStore

        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { login(username: "auth_mut_test", password: "testpass123") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['login']['username'], 'auth_mut_test')

    def test_login_with_invalid_credentials(self):
        from django.test import RequestFactory
        from django.contrib.sessions.backends.db import SessionStore

        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { login(username: "auth_mut_test", password: "wrongpass") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['login'])

    def test_logout(self):
        from django.test import RequestFactory
        from django.contrib.sessions.backends.db import SessionStore

        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        request.user = self.user
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { logout }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['logout'])

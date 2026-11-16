"""Superset embedding: dashboards query, guest-token mutation, config mutation, embed command.

Superset is mocked at the HTTP layer (requests.Session.request), so the real
SupersetRestClient runs: service-account login, CSRF token, guest token.
"""
import json
import uuid
from io import StringIO
from unittest.mock import patch

import requests
from config.schema import schema
from core.models import SupersetDashboard
from core.schema.context import StrawberryContext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.contrib.sessions.backends.db import SessionStore
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.utils import timezone
from organization.models import Organization, OrganizationMember

User = get_user_model()

SUPERSET = {
    'SUPERSET_URL': 'http://superset.test:8088',
    'SUPERSET_PUBLIC_URL': 'https://analytics.example.com/',
    'SUPERSET_USERNAME': 'embed-service',
    'SUPERSET_PASSWORD': 'service-password',
    'SUPERSET_EMBED_ALLOWED_DOMAINS': ['http://localhost:3000'],
}

DASHBOARDS_QUERY = '{ supersetDashboards { guid embeddedId title order supersetDomain } }'
GUEST_TOKEN = 'mutation($d: ID!) { supersetGuestToken(dashboard: $d) { ok token errors { field messages } } }'
SAVE_DASHBOARD = 'mutation($i: JSON!) { supersetDashboard(input: $i) { ok errors { field messages } } }'


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload


class FakeSuperset:
    """Records calls and answers like Superset's REST API."""

    def __init__(self, guest_status=200, embedded_uuid=None):
        self.calls = []
        self.guest_status = guest_status
        self.embedded_uuid = embedded_uuid or str(uuid.uuid4())

    def __call__(self, session, method, url, **kwargs):
        self.calls.append({'method': method, 'url': url, 'headers': dict(session.headers), **kwargs})
        path = url.removeprefix(SUPERSET['SUPERSET_URL'])
        if path == '/api/v1/security/login':
            return FakeResponse(200, {'access_token': 'service-access-token'})
        if path == '/api/v1/security/csrf_token/':
            return FakeResponse(200, {'result': 'csrf-123'})
        if path == '/api/v1/security/guest_token/':
            if self.guest_status != 200:
                return FakeResponse(self.guest_status, {'message': 'Forbidden'})
            return FakeResponse(200, {'token': 'guest-token-abc'})
        if path == '/api/v1/dashboard/sales':
            return FakeResponse(200, {'result': {'id': 7, 'dashboard_title': 'Sales'}})
        if path == '/api/v1/dashboard/7/embedded':
            return FakeResponse(200, {'result': {'uuid': self.embedded_uuid}})
        return FakeResponse(404, {'message': 'Not found'})

    def call(self, path):
        return next(c for c in self.calls if c['url'].endswith(path))


@override_settings(**SUPERSET)
class SupersetTestBase(TestCase):

    def setUp(self):
        self.admin = User.objects.create_superuser('superset-admin', 'admin@example.com', 'x')
        self.member = User.objects.create_user('superset-member', 'member@example.com', 'x')
        self.org = Organization.objects.create(name='Acme')
        OrganizationMember.objects.create(organization=self.org, member=self.admin, is_active=True)
        self.dashboard = SupersetDashboard.objects.create(
            embedded_id=uuid.uuid4(), title='Revenue', order=1,
        )

    def execute(self, query, user, **variables):
        return schema.execute_sync(
            query, variable_values=variables, context_value=StrawberryContext(FakeRequest(user)),
        )

    def grant(self, user, codename):
        group = Group.objects.create(name=f'superset-{codename}')
        group.permissions.add(Permission.objects.get(codename=codename))
        user.groups.add(group)
        return User.objects.get(pk=user.pk)  # drop the cached permissions

    def superset(self, fake):
        return patch.object(requests.Session, 'request', autospec=True, side_effect=fake)


class SupersetDashboardsQueryTest(SupersetTestBase):

    def test_requires_authentication(self):
        result = self.execute(DASHBOARDS_QUERY, AnonymousUser())
        self.assertIn('Authentication required', str(result.errors))

    def test_lists_live_dashboards_in_order_with_public_domain(self):
        SupersetDashboard.objects.create(embedded_id=uuid.uuid4(), title='Ops', order=0)
        SupersetDashboard.objects.create(embedded_id=uuid.uuid4(), title='Gone', deleted_at=timezone.now())
        result = self.execute(DASHBOARDS_QUERY, self.admin)
        self.assertIsNone(result.errors)
        rows = result.data['supersetDashboards']
        self.assertEqual([r['title'] for r in rows], ['Ops', 'Revenue'])
        self.assertEqual(rows[1]['guid'], str(self.dashboard.guid))
        self.assertEqual(rows[1]['embeddedId'], str(self.dashboard.embedded_id))
        self.assertEqual(rows[1]['supersetDomain'], 'https://analytics.example.com')

    def test_never_exposes_secrets_or_rls(self):
        result = schema.as_str()
        type_sdl = result[result.index('type SupersetDashboardType'):].split('}')[0]
        self.assertNotIn('rlsClause', type_sdl)
        self.assertNotIn('password', type_sdl.lower())

    def test_user_without_view_permission_sees_nothing(self):
        result = self.execute(DASHBOARDS_QUERY, self.member)
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['supersetDashboards'], [])

    def test_user_with_view_permission_sees_dashboards(self):
        member = self.grant(self.member, 'view_supersetdashboard')
        result = self.execute(DASHBOARDS_QUERY, member)
        self.assertEqual([r['title'] for r in result.data['supersetDashboards']], ['Revenue'])


class SupersetGuestTokenTest(SupersetTestBase):

    def test_requires_authentication(self):
        result = self.execute(GUEST_TOKEN, AnonymousUser(), d=str(self.dashboard.guid))
        self.assertIn('Authentication required', str(result.errors))

    def test_requires_view_permission(self):
        fake = FakeSuperset()
        with self.superset(fake):
            result = self.execute(GUEST_TOKEN, self.member, d=str(self.dashboard.guid))
        self.assertIsNotNone(result.errors)
        self.assertEqual(fake.calls, [])

    def test_issues_token_through_service_account(self):
        fake = FakeSuperset()
        with self.superset(fake):
            result = self.execute(GUEST_TOKEN, self.admin, d=str(self.dashboard.guid))
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['supersetGuestToken'], {'ok': True, 'token': 'guest-token-abc', 'errors': []})

        login = fake.call('/api/v1/security/login')
        self.assertEqual(login['json']['username'], 'embed-service')
        self.assertEqual(login['json']['password'], 'service-password')
        guest = fake.call('/api/v1/security/guest_token/')
        self.assertEqual(guest['method'], 'POST')
        self.assertEqual(guest['headers']['Authorization'], 'Bearer service-access-token')
        self.assertEqual(guest['headers']['X-CSRFToken'], 'csrf-123')
        self.assertEqual(guest['json']['resources'], [{'type': 'dashboard', 'id': str(self.dashboard.embedded_id)}])
        self.assertEqual(guest['json']['rls'], [])
        self.assertEqual(guest['json']['user']['username'], 'superset-admin')
        self.assertTrue(all(c['timeout'] for c in fake.calls))

    def test_rls_clause_scopes_to_active_organization(self):
        self.dashboard.rls_clause = 'organization_guid = {organization_guid}'
        self.dashboard.save()
        fake = FakeSuperset()
        with self.superset(fake):
            self.execute(GUEST_TOKEN, self.admin, d=str(self.dashboard.guid))
        rls = fake.call('/api/v1/security/guest_token/')['json']['rls']
        self.assertEqual(rls, [{'clause': f"organization_guid = '{self.org.guid}'"}])

    def test_rls_clause_without_organization_returns_no_rows(self):
        self.dashboard.rls_clause = 'organization_guid = {organization_guid}'
        self.dashboard.save()
        member = self.grant(self.member, 'view_supersetdashboard')
        fake = FakeSuperset()
        with self.superset(fake):
            self.execute(GUEST_TOKEN, member, d=str(self.dashboard.guid))
        self.assertEqual(fake.call('/api/v1/security/guest_token/')['json']['rls'], [{'clause': '1 = 0'}])

    def test_superset_failure_returns_generic_error(self):
        with self.superset(FakeSuperset(guest_status=403)), self.assertLogs('core', level='ERROR'):
            result = self.execute(GUEST_TOKEN, self.admin, d=str(self.dashboard.guid))
        payload = result.data['supersetGuestToken']
        self.assertFalse(payload['ok'])
        self.assertIsNone(payload['token'])
        self.assertEqual(payload['errors'][0]['messages'], ['Analytics are unavailable right now.'])
        self.assertNotIn('service-password', json.dumps(payload))

    def test_unreachable_superset_returns_error(self):
        with patch.object(requests.Session, 'request', side_effect=requests.ConnectionError('refused')):
            result = self.execute(GUEST_TOKEN, self.admin, d=str(self.dashboard.guid))
        self.assertFalse(result.data['supersetGuestToken']['ok'])

    @override_settings(SUPERSET_URL='')
    def test_unconfigured_superset_returns_error(self):
        result = self.execute(GUEST_TOKEN, self.admin, d=str(self.dashboard.guid))
        self.assertFalse(result.data['supersetGuestToken']['ok'])

    def test_unknown_deleted_or_malformed_dashboard(self):
        deleted = SupersetDashboard.objects.create(embedded_id=uuid.uuid4(), title='Old', deleted_at=timezone.now())
        fake = FakeSuperset()
        with self.superset(fake):
            for guid in (str(uuid.uuid4()), str(deleted.guid), 'not-a-uuid'):
                result = self.execute(GUEST_TOKEN, self.admin, d=guid)
                self.assertEqual(result.data['supersetGuestToken']['errors'][0]['messages'], ['Dashboard not found.'])
        self.assertEqual(fake.calls, [])


class SupersetDashboardMutationTest(SupersetTestBase):

    def test_creates_dashboard(self):
        embedded_id = str(uuid.uuid4())
        result = self.execute(SAVE_DASHBOARD, self.admin, i={'embedded_id': embedded_id, 'title': 'Churn'})
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['supersetDashboard']['ok'], result.data)
        self.assertTrue(SupersetDashboard.objects.filter(embedded_id=embedded_id, title='Churn').exists())

    def test_updates_dashboard_by_guid(self):
        result = self.execute(SAVE_DASHBOARD, self.admin, i={'guid': str(self.dashboard.guid), 'title': 'Revenue v2', 'order': 5})
        self.assertTrue(result.data['supersetDashboard']['ok'], result.data)
        self.dashboard.refresh_from_db()
        self.assertEqual((self.dashboard.title, self.dashboard.order), ('Revenue v2', 5))

    def test_rejects_unknown_guid(self):
        result = self.execute(SAVE_DASHBOARD, self.admin, i={'guid': str(uuid.uuid4()), 'title': 'X'})
        self.assertFalse(result.data['supersetDashboard']['ok'])

    def test_requires_add_permission(self):
        result = self.execute(SAVE_DASHBOARD, self.member, i={'embedded_id': str(uuid.uuid4()), 'title': 'Nope'})
        self.assertIsNotNone(result.errors)
        self.assertFalse(SupersetDashboard.objects.filter(title='Nope').exists())


@override_settings(**SUPERSET)
class SupersetEmbedCommandTest(TestCase):

    def test_enables_embedding_and_registers_dashboard(self):
        fake = FakeSuperset()
        out = StringIO()
        with patch.object(requests.Session, 'request', autospec=True, side_effect=fake):
            call_command('superset_embed', 'sales', '--order', '3', stdout=out)
            call_command('superset_embed', 'sales', stdout=out)  # idempotent

        self.assertEqual(fake.call('/api/v1/dashboard/7/embedded')['json'], {'allowed_domains': ['http://localhost:3000']})
        dashboard = SupersetDashboard.objects.get(embedded_id=fake.embedded_uuid)
        self.assertEqual((dashboard.title, dashboard.order), ('Sales', 3))
        self.assertEqual(SupersetDashboard.objects.count(), 1)

    def test_unknown_dashboard_fails(self):
        with patch.object(requests.Session, 'request', autospec=True, side_effect=FakeSuperset()), \
                self.assertLogs('core', level='ERROR'), self.assertRaises(CommandError):
            call_command('superset_embed', 'missing', stdout=StringIO())

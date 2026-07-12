"""Integration tests for the `me` query (current authenticated user).

Added for the frontend GET_ME alignment (#107): the schema previously had no
current-user query at all — UserType was only reachable via mutation results.
"""
from config.schema import schema
from core.schema.common import GlobalIDUtils
from core.schema.context import StrawberryContext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class MeQueryTest(TestCase):
    """Tests for the me query."""

    QUERY = 'query { me { id username email isAnonymous } }'

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='MeOrg')
        self.user = User.objects.create_user(
            username='me_query_user', email='me@test.com', password='x',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def _execute(self, user):
        return schema.execute_sync(
            self.QUERY, context_value=StrawberryContext(FakeRequest(user)),
        )

    def test_authenticated_returns_current_user(self):
        """An authenticated request resolves the session user."""
        result = self._execute(self.user)
        self.assertIsNone(result.errors)
        data = result.data['me']
        self.assertEqual(data['username'], 'me_query_user')
        self.assertEqual(data['email'], 'me@test.com')
        self.assertFalse(data['isAnonymous'])

    def test_id_is_relay_global_id(self):
        """UserType.id is the relay global id, never the integer pk."""
        result = self._execute(self.user)
        self.assertIsNone(result.errors)
        gid = result.data['me']['id']
        self.assertNotEqual(gid, str(self.user.pk))
        type_name, pk = GlobalIDUtils.from_global_id(gid)
        self.assertEqual(type_name, 'UserType')
        self.assertEqual(int(pk), self.user.pk)

    def test_anonymous_returns_null(self):
        """An unauthenticated request resolves to null (logged-out signal)."""
        result = self._execute(AnonymousUser())
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['me'])

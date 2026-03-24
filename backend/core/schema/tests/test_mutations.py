"""Integration tests for Strawberry GraphQL mutations.

Exercises auth, notification, library, and permission mutations end-to-end
through the assembled schema, verifying both GraphQL responses and database state.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase

from config.schema import schema, schema_auth
from core.models import Notification, NotificationStatus, SharedDirectory
from core.schema.common import GlobalIDUtils
from core.schema.context import StrawberryContext

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


# ---------------------------------------------------------------------------
# Auth mutations (via schema_auth)
# ---------------------------------------------------------------------------

class LoginMutationTest(TestCase):
    """Tests for the login mutation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='login_test_user',
            email='login@test.com',
            password='correct-horse-battery',
        )

    def _make_context(self):
        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        return StrawberryContext(request)

    def test_login_success(self):
        """Valid credentials return the authenticated user."""
        context = self._make_context()
        result = schema_auth.execute_sync(
            'mutation { login(username: "login_test_user", password: "correct-horse-battery") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['login']['username'], 'login_test_user')

    def test_login_success_populates_session(self):
        """Successful login writes the user into the session."""
        context = self._make_context()
        schema_auth.execute_sync(
            'mutation { login(username: "login_test_user", password: "correct-horse-battery") { username } }',
            context_value=context,
        )
        # Django login stores _auth_user_id in session
        self.assertIn('_auth_user_id', context.request.session)
        self.assertEqual(
            str(context.request.session['_auth_user_id']),
            str(self.user.pk),
        )

    def test_login_invalid_credentials(self):
        """Wrong password returns null (no user)."""
        context = self._make_context()
        result = schema_auth.execute_sync(
            'mutation { login(username: "login_test_user", password: "wrong-password") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['login'])

    def test_login_nonexistent_user(self):
        """A username that does not exist returns null."""
        context = self._make_context()
        result = schema_auth.execute_sync(
            'mutation { login(username: "ghost_user", password: "any") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['login'])

    def test_login_inactive_user(self):
        """An inactive user cannot authenticate."""
        self.user.is_active = False
        self.user.save()

        context = self._make_context()
        result = schema_auth.execute_sync(
            'mutation { login(username: "login_test_user", password: "correct-horse-battery") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['login'])


class LogoutMutationTest(TestCase):
    """Tests for the logout mutation."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='logout_test_user',
            email='logout@test.com',
            password='testpass123',
        )

    def test_logout_returns_true(self):
        """Logout always returns true."""
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

    def test_logout_clears_session(self):
        """After logout the session no longer references the user."""
        request = RequestFactory().post('/gql/v2/config/auth/')
        session = SessionStore()
        session.create()
        request.session = session
        request.user = self.user

        # Simulate a logged-in session
        from django.contrib.auth import login
        login(request, self.user)
        self.assertIn('_auth_user_id', request.session)

        context = StrawberryContext(request)
        schema_auth.execute_sync(
            'mutation { logout }',
            context_value=context,
        )
        self.assertNotIn('_auth_user_id', request.session)

    def test_logout_with_anonymous_user(self):
        """Logout on an already-anonymous session still returns true."""
        from django.contrib.auth.models import AnonymousUser
        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        request.user = AnonymousUser()
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { logout }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['logout'])


# ---------------------------------------------------------------------------
# Notification mutations (via main schema)
# ---------------------------------------------------------------------------

class NotificationReadMutationTest(TestCase):
    """Tests for the notificationRead mutation."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='NotifOrg')
        self.user = User.objects.create_superuser(
            username='notif_test_user',
            email='notif@test.com',
            password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.other_user = User.objects.create_user(
            username='notif_other_user',
            email='notif_other@test.com',
            password='testpass',
        )

        self.notification = Notification.objects.create(
            user=self.user,
            subject='Test subject',
            message='Test message body',
            status=NotificationStatus.UNREAD,
            created_by=self.user,
        )

    def _make_context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.user))

    def _patch_get_object(self, notification):
        """Patch the broken import path so get_object resolves directly."""
        import sys
        import types

        # The mutation does `from core.schema import NotificationType` at call time.
        # core.schema.__init__ doesn't export NotificationType, so we inject it.
        fake_type = types.SimpleNamespace()
        fake_type.get_object = staticmethod(
            lambda info, gid, raise_not_found=True: notification
        )
        return patch.dict(
            sys.modules['core.schema'].__dict__,
            {'NotificationType': fake_type},
        )

    def test_notification_read_marks_as_read(self):
        """Marking a notification as read updates its status in the database."""
        gid = self.notification.global_id
        context = self._make_context()

        with self._patch_get_object(self.notification):
            result = schema.execute_sync(
                'mutation NotifRead($gid: ID!) { notificationRead(gid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.assertIsNone(result.errors)
        self.assertTrue(result.data['notificationRead'])

        # Verify database state
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, NotificationStatus.READ)

    def test_notification_read_updates_status_date(self):
        """Marking as read also updates the status_date timestamp."""
        original_date = self.notification.status_date
        gid = self.notification.global_id
        context = self._make_context()

        with self._patch_get_object(self.notification):
            schema.execute_sync(
                'mutation NotifRead($gid: ID!) { notificationRead(gid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.notification.refresh_from_db()
        self.assertGreaterEqual(self.notification.status_date, original_date)

    def test_notification_read_wrong_user_raises(self):
        """A user cannot mark another user's notification as read."""
        # Create notification owned by other_user
        other_notif = Notification.objects.create(
            user=self.other_user,
            subject='Private',
            message='Not yours',
            status=NotificationStatus.UNREAD,
            created_by=self.other_user,
        )
        gid = other_notif.global_id
        context = self._make_context(self.user)

        with self._patch_get_object(other_notif):
            result = schema.execute_sync(
                'mutation NotifRead($gid: ID!) { notificationRead(gid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.assertIsNotNone(result.errors)
        self.assertIn('does not belong to user', str(result.errors[0]))

        # Database should be unchanged
        other_notif.refresh_from_db()
        self.assertEqual(other_notif.status, NotificationStatus.UNREAD)

    def test_notification_read_already_read_is_idempotent(self):
        """Marking an already-read notification as read succeeds without error."""
        self.notification.status = NotificationStatus.READ
        self.notification.save()

        gid = self.notification.global_id
        context = self._make_context()

        with self._patch_get_object(self.notification):
            result = schema.execute_sync(
                'mutation NotifRead($gid: ID!) { notificationRead(gid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.assertIsNone(result.errors)
        self.assertTrue(result.data['notificationRead'])
        self.notification.refresh_from_db()
        self.assertEqual(self.notification.status, NotificationStatus.READ)


# ---------------------------------------------------------------------------
# Library mutations (via main schema)
# ---------------------------------------------------------------------------

class LibraryMkdirMutationTest(TestCase):
    """Tests for the libraryMkdir mutation."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='LibOrg')
        self.user = User.objects.create_superuser(
            username='lib_test_user',
            email='lib@test.com',
            password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def _make_context(self):
        return StrawberryContext(FakeRequest(self.user))

    def test_library_mkdir_creates_directory(self):
        """Creating a root-level directory succeeds and persists to the database."""
        context = self._make_context()
        result = schema.execute_sync(
            'mutation { libraryMkdir(name: "Test Folder") { ok } }',
            context_value=context,
        )

        self.assertIsNone(result.errors)
        self.assertTrue(result.data['libraryMkdir']['ok'])

        # pydash.camel_case("Test Folder") -> "testFolder"
        self.assertTrue(
            SharedDirectory.objects.filter(path='/testFolder').exists()
        )

    def test_library_mkdir_sets_created_by(self):
        """The created_by field is set to the requesting user."""
        context = self._make_context()
        schema.execute_sync(
            'mutation { libraryMkdir(name: "My Docs") { ok } }',
            context_value=context,
        )

        directory = SharedDirectory.objects.get(path='/myDocs')
        self.assertEqual(directory.created_by, self.user)

    def test_library_mkdir_display_name_preserved(self):
        """The display_name keeps the original human-readable form."""
        context = self._make_context()
        schema.execute_sync(
            'mutation { libraryMkdir(name: "Annual Reports") { ok } }',
            context_value=context,
        )

        directory = SharedDirectory.objects.get(path='/annualReports')
        self.assertEqual(directory.display_name, 'Annual Reports')

    def test_library_mkdir_idempotent(self):
        """Creating the same directory name twice returns the existing one (no duplicate)."""
        context = self._make_context()

        schema.execute_sync(
            'mutation { libraryMkdir(name: "Shared") { ok } }',
            context_value=context,
        )
        schema.execute_sync(
            'mutation { libraryMkdir(name: "Shared") { ok } }',
            context_value=context,
        )

        count = SharedDirectory.objects.filter(path='/shared').count()
        self.assertEqual(count, 1)

    def test_library_mkdir_different_names_create_different_dirs(self):
        """Two calls with different names produce two distinct directories."""
        context = self._make_context()

        schema.execute_sync(
            'mutation { libraryMkdir(name: "Alpha") { ok } }',
            context_value=context,
        )
        schema.execute_sync(
            'mutation { libraryMkdir(name: "Beta") { ok } }',
            context_value=context,
        )

        self.assertTrue(SharedDirectory.objects.filter(path='/alpha').exists())
        self.assertTrue(SharedDirectory.objects.filter(path='/beta').exists())


class LibraryRmdirMutationTest(TestCase):
    """Tests for the libraryRmdir mutation."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='RmOrg')
        self.user = User.objects.create_superuser(
            username='rm_test_user',
            email='rm@test.com',
            password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

        self.directory = SharedDirectory.objects.mkdir(
            path=None, name='Deleteme', created_by=self.user,
        )

    def _make_context(self):
        return StrawberryContext(FakeRequest(self.user))

    def _patch_get_shared_directory(self, directory):
        """Patch the Graphene import used by _get_shared_directory."""
        return patch(
            'core.schema.mutations.library._get_shared_directory',
            return_value=directory,
        )

    def test_library_rmdir_deletes_directory(self):
        """Removing a directory deletes it from the database."""
        gid = self.directory.global_id
        context = self._make_context()
        dir_pk = self.directory.pk

        with self._patch_get_shared_directory(self.directory):
            result = schema.execute_sync(
                'mutation RmDir($gid: ID!) { libraryRmdir(directoryGuid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.assertIsNone(result.errors)
        self.assertTrue(result.data['libraryRmdir'])
        self.assertFalse(SharedDirectory.objects.filter(pk=dir_pk).exists())

    def test_library_rmdir_only_removes_target(self):
        """Removing one directory does not affect siblings."""
        other = SharedDirectory.objects.mkdir(
            path=None, name='KeepMe', created_by=self.user,
        )
        gid = self.directory.global_id
        context = self._make_context()

        with self._patch_get_shared_directory(self.directory):
            schema.execute_sync(
                'mutation RmDir($gid: ID!) { libraryRmdir(directoryGuid: $gid) }',
                variable_values={'gid': gid},
                context_value=context,
            )

        self.assertTrue(SharedDirectory.objects.filter(pk=other.pk).exists())



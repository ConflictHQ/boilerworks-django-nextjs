"""Integration tests for Strawberry type resolvers.

Exercises field-level permission checks, dataloader-based resolution, and
queryset scoping on AddressType, UserType, ProfileType, OrganizationType,
and NotificationType.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase

from config.schema import schema, schema_auth
from core.models import Address, Notification, NotificationStatus
from core.schema.context import StrawberryContext
from core.schema.types.notification import NotificationType

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class FakeInfo:
    """Minimal Info mock that carries a StrawberryContext."""

    def __init__(self, context):
        self.context = context


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_context(user):
    return StrawberryContext(FakeRequest(user))


def _get_resolver(strawberry_type, field_name):
    """Extract the raw Python function from a Strawberry type's field.

    strawberry_django.field decorates the method and stores it inside
    ``__strawberry_definition__.fields[].base_resolver.wrapped_func``.
    """
    for field in strawberry_type.__strawberry_definition__.fields:
        if field.name == field_name:
            return field.base_resolver.wrapped_func
    raise ValueError(f'{strawberry_type.__name__} has no field {field_name!r}')


def _setup_superuser(username='resolver_super', email='resolver_super@test.com'):
    from organization.models import Organization, OrganizationMember

    user = User.objects.create_superuser(
        username=username, email=email, password='testpass',
    )
    org = Organization.objects.create(name=f'Org-{username}')
    OrganizationMember.objects.create(
        organization=org, member=user, is_active=True,
    )
    user.profile.active_organization = org
    user.profile.save()
    return user, org


def _setup_regular_user(username='resolver_regular', email='resolver_regular@test.com'):
    from organization.models import Organization, OrganizationMember

    user = User.objects.create_user(
        username=username, email=email, password='testpass',
    )
    org = Organization.objects.create(name=f'Org-{username}')
    OrganizationMember.objects.create(
        organization=org, member=user, is_active=True,
    )
    user.profile.active_organization = org
    user.profile.save()
    return user, org


# ---------------------------------------------------------------------------
# AddressType — permission-gated field resolvers
# ---------------------------------------------------------------------------

class AddressFieldPermittedTest(TestCase):
    """Superuser can read all permission-gated address fields."""

    def setUp(self):
        from core.schema.types.address import AddressType
        self.AddressType = AddressType

        self.user, self.org = _setup_superuser()
        self.address = Address.objects.create(
            address_line_one='123 Main St',
            address_line_two='Apt 4',
            city='Springfield',
            state='IL',
            street='Main St',
            zipcode='62704',
        )
        self.user.profile.address = self.address
        self.user.profile.save()
        self.info = FakeInfo(_make_context(self.user))

    def _resolve(self, field_name):
        fn = _get_resolver(self.AddressType, field_name)
        return fn(self.address, info=self.info)

    def test_address_field_returns_value_when_permitted_address_line_one(self):
        self.assertEqual(self._resolve('address_line_one'), self.address.address_line_one)

    def test_address_field_returns_value_when_permitted_address_line_two(self):
        self.assertEqual(self._resolve('address_line_two'), self.address.address_line_two)

    def test_address_field_returns_value_when_permitted_city(self):
        self.assertEqual(self._resolve('city'), self.address.city)

    def test_address_field_returns_value_when_permitted_state(self):
        self.assertEqual(self._resolve('state'), self.address.state)

    def test_address_field_returns_value_when_permitted_street(self):
        self.assertEqual(self._resolve('street'), self.address.street)

    def test_address_field_returns_value_when_permitted_zipcode(self):
        self.assertEqual(self._resolve('zipcode'), self.address.zipcode)


class AddressFieldDeniedTest(TestCase):
    """When permission check returns False, address fields return empty string."""

    def setUp(self):
        from core.schema.types.address import AddressType
        self.AddressType = AddressType

        self.user, self.org = _setup_superuser(
            username='addr_denied', email='addr_denied@test.com',
        )
        self.address = Address.objects.create(
            address_line_one='456 Oak Ave',
            address_line_two='Suite 7',
            city='Shelbyville',
            state='IN',
            street='Oak Ave',
            zipcode='46176',
        )
        self.user.profile.address = self.address
        self.user.profile.save()
        self.info = FakeInfo(_make_context(self.user))

    def _resolve_denied(self, field_name):
        fn = _get_resolver(self.AddressType, field_name)
        with patch.object(Address, 'p') as mock_p:
            mock_p.return_value.view.by.return_value = False
            return fn(self.address, info=self.info)

    def test_address_field_returns_empty_when_denied_address_line_one(self):
        self.assertEqual(self._resolve_denied('address_line_one'), '')

    def test_address_field_returns_empty_when_denied_address_line_two(self):
        self.assertEqual(self._resolve_denied('address_line_two'), '')

    def test_address_field_returns_empty_when_denied_city(self):
        self.assertEqual(self._resolve_denied('city'), '')

    def test_address_field_returns_empty_when_denied_state(self):
        self.assertEqual(self._resolve_denied('state'), '')

    def test_address_field_returns_empty_when_denied_street(self):
        self.assertEqual(self._resolve_denied('street'), '')

    def test_address_field_returns_empty_when_denied_zipcode(self):
        self.assertEqual(self._resolve_denied('zipcode'), '')


# ---------------------------------------------------------------------------
# UserType — basic field resolution
# ---------------------------------------------------------------------------

class UserTypeIsNewUserTest(TestCase):
    """is_new_user reflects whether the username still matches the profile guid hex."""

    def setUp(self):
        from core.schema.types.user import UserType
        self.UserType = UserType

        self.user, self.org = _setup_superuser(
            username='user_new_test', email='usernew@test.com',
        )
        self.info = FakeInfo(_make_context(self.user))

    def test_user_is_new_user_false_when_username_set(self):
        """A user whose username differs from profile guid hex is NOT new."""
        fn = _get_resolver(self.UserType, 'is_new_user')
        self.assertNotEqual(self.user.username, self.user.profile.gid.hex)
        self.assertFalse(fn(self.user, info=self.info))

    def test_user_is_new_user_true_when_username_matches_guid(self):
        """A user whose username equals profile guid hex IS new."""
        fn = _get_resolver(self.UserType, 'is_new_user')
        self.user.username = self.user.profile.gid.hex
        self.user.save()
        self.assertTrue(fn(self.user, info=self.info))


class UserTypeEmailTest(TestCase):
    """UserType.email resolves to the user's email via auth schema login."""

    def setUp(self):
        self.user, self.org = _setup_superuser(
            username='user_email_test', email='email_resolve@test.com',
        )

    def test_user_email(self):
        from django.test import RequestFactory

        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { login(username: "user_email_test", password: "testpass") { email } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['login']['email'], self.user.email)


class UserTypeUsernameTest(TestCase):
    """UserType.username resolves to the user's username via auth schema login."""

    def setUp(self):
        self.user, self.org = _setup_superuser(
            username='username_resolve_test', email='uname@test.com',
        )

    def test_user_username(self):
        from django.test import RequestFactory

        request = RequestFactory().post('/gql/v2/config/auth/')
        request.session = SessionStore()
        context = StrawberryContext(request)

        result = schema_auth.execute_sync(
            'mutation { login(username: "username_resolve_test", password: "testpass") { username } }',
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['login']['username'], self.user.username)


# ---------------------------------------------------------------------------
# ProfileType — permission-gated and computed fields
# ---------------------------------------------------------------------------

class ProfileEmailPermittedTest(TestCase):
    """Superuser can see profile email (resolved from user.email)."""

    def setUp(self):
        from core.schema.types.user import ProfileType
        self.ProfileType = ProfileType

        self.user, self.org = _setup_superuser(
            username='prof_email', email='profile_email@test.com',
        )
        self.info = FakeInfo(_make_context(self.user))

    def test_profile_email_permitted(self):
        fn = _get_resolver(self.ProfileType, 'email')
        result = fn(self.user.profile, info=self.info)
        self.assertEqual(result, self.user.email)


class ProfileEmailDeniedTest(TestCase):
    """When permission is denied, profile email returns None."""

    def setUp(self):
        from core.schema.types.user import ProfileType
        self.ProfileType = ProfileType

        self.user, self.org = _setup_superuser(
            username='prof_email_denied', email='denied_email@test.com',
        )
        self.info = FakeInfo(_make_context(self.user))

    def test_profile_email_denied(self):
        from core.models import Profile

        fn = _get_resolver(self.ProfileType, 'email')
        with patch.object(Profile, 'p') as mock_p:
            mock_p.return_value.view.by.return_value = False
            result = fn(self.user.profile, info=self.info)
        self.assertIsNone(result)


class ProfileHasPinTest(TestCase):
    """has_pin returns True when pin is set, False otherwise."""

    def setUp(self):
        from core.schema.types.user import ProfileType
        self.ProfileType = ProfileType

        self.user, self.org = _setup_superuser(
            username='prof_pin', email='prof_pin@test.com',
        )

    def test_profile_has_pin_true(self):
        fn = _get_resolver(self.ProfileType, 'has_pin')
        profile = self.user.profile
        profile.pin = 'hashed-pin-value'
        profile.save()
        self.assertTrue(fn(profile))

    def test_profile_has_pin_false(self):
        fn = _get_resolver(self.ProfileType, 'has_pin')
        profile = self.user.profile
        profile.pin = None
        profile.save()
        self.assertFalse(fn(profile))

    def test_profile_has_pin_false_empty_string(self):
        fn = _get_resolver(self.ProfileType, 'has_pin')
        profile = self.user.profile
        profile.pin = ''
        profile.save()
        self.assertFalse(fn(profile))


class ProfileTimezoneDefaultTest(TestCase):
    """Profile timezone defaults to empty string."""

    def setUp(self):
        self.user, self.org = _setup_superuser(
            username='prof_tz', email='prof_tz@test.com',
        )

    def test_profile_timezone_default(self):
        profile = self.user.profile
        self.assertEqual(profile.timezone, '')


# ---------------------------------------------------------------------------
# Organization queries — search and slug lookup
# ---------------------------------------------------------------------------

class OrganizationsQuerySearchTest(TestCase):
    """The organizations query filters by search term."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.user, _ = _setup_superuser(
            username='org_search', email='org_search@test.com',
        )
        self.org_alpha = Organization.objects.create(name='AlphaCorp')
        self.org_beta = Organization.objects.create(name='BetaIndustries')
        OrganizationMember.objects.get_or_create(
            organization=self.org_alpha, member=self.user, defaults={'is_active': True},
        )
        self.context = _make_context(self.user)

    def test_organizations_query_filters_by_search(self):
        result = schema.execute_sync(
            '{ organizations(query: "Alpha") { name slug } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        org_names = [o['name'] for o in result.data['organizations']]
        self.assertIn('AlphaCorp', org_names)
        self.assertNotIn('BetaIndustries', org_names)

    def test_organizations_query_returns_all_without_search(self):
        result = schema.execute_sync(
            '{ organizations { name } }',
            context_value=self.context,
        )
        self.assertIsNone(result.errors)
        org_names = [o['name'] for o in result.data['organizations']]
        self.assertIn('AlphaCorp', org_names)
        self.assertIn('BetaIndustries', org_names)


class OrganizationBySlugTest(TestCase):
    """Single organization lookup via the organization(id:) query."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        from core.schema.common import GlobalIDUtils

        self.user, _ = _setup_superuser(
            username='org_slug', email='org_slug@test.com',
        )
        self.org = Organization.objects.create(name='SlugTestOrg')
        OrganizationMember.objects.get_or_create(
            organization=self.org, member=self.user, defaults={'is_active': True},
        )
        self.global_id = GlobalIDUtils.to_global_id('OrganizationType', self.org.pk)
        self.context = _make_context(self.user)

    def test_organization_by_id(self):
        query = '''
            query Org($id: ID!) {
                organization(id: $id) { name slug }
            }
        '''
        result = schema.execute_sync(
            query,
            context_value=self.context,
            variable_values={'id': self.global_id},
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['organization']['name'], self.org.name)
        self.assertEqual(result.data['organization']['slug'], self.org.slug)

    def test_organization_by_id_returns_null_for_missing(self):
        from core.schema.common import GlobalIDUtils

        bogus_id = GlobalIDUtils.to_global_id('OrganizationType', 999999)
        query = '''
            query Org($id: ID!) {
                organization(id: $id) { name }
            }
        '''
        result = schema.execute_sync(
            query,
            context_value=self.context,
            variable_values={'id': bogus_id},
        )
        self.assertIsNone(result.errors)
        self.assertIsNone(result.data['organization'])


# ---------------------------------------------------------------------------
# NotificationType — queryset scoping to current user
# ---------------------------------------------------------------------------

class NotificationScopedToCurrentUserTest(TestCase):
    """NotificationType.get_queryset filters to the requesting user only."""

    def setUp(self):
        self.user_a, self.org_a = _setup_superuser(
            username='notif_user_a', email='notif_a@test.com',
        )
        self.user_b, self.org_b = _setup_regular_user(
            username='notif_user_b', email='notif_b@test.com',
        )

        self.notif_a = Notification.objects.create(
            user=self.user_a,
            subject='For User A',
            message='Message for A',
            created_by=self.user_b,
        )
        self.notif_b = Notification.objects.create(
            user=self.user_b,
            subject='For User B',
            message='Message for B',
            created_by=self.user_a,
        )

    def test_notification_scoped_to_current_user(self):
        """get_queryset returns only notifications belonging to the requesting user."""
        info_a = FakeInfo(_make_context(self.user_a))
        filtered = NotificationType.get_queryset(Notification.objects.all(), info_a)

        self.assertIn(self.notif_a, filtered)
        self.assertNotIn(self.notif_b, filtered)

    def test_notification_scoped_excludes_other_users(self):
        """User B's context only returns user B's notifications."""
        info_b = FakeInfo(_make_context(self.user_b))
        filtered = NotificationType.get_queryset(Notification.objects.all(), info_b)

        self.assertNotIn(self.notif_a, filtered)
        self.assertIn(self.notif_b, filtered)

    def test_notification_count_matches_user(self):
        """Each user sees exactly one notification."""
        for usr in (self.user_a, self.user_b):
            info = FakeInfo(_make_context(usr))
            filtered = NotificationType.get_queryset(Notification.objects.all(), info)
            self.assertEqual(filtered.count(), 1)

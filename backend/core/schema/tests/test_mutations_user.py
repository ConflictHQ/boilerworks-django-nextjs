"""Integration tests for user mutations (issue #67).

Exercises upsertUser, profile, switchUser, pinTransaction and the signRequest
mutations end-to-end through the assembled schema — happy paths plus
permission-denied paths.

The mutations still import legacy Graphene type helpers from the nonexistent
`core.schema.user` module; a fake module is injected the same way
test_mutations.py / test_mutations_upload.py handle `core.schema`.
"""
import sys
import types
from unittest.mock import patch

from config.schema import schema
from core.models import GlobalIDLink, PinTransaction, Profile, SignRequest
from core.models.user import PinTransactionKindChoices, SignRequestMixin, SignRequestStatusChoices
from core.schema.common import GlobalIDUtils
from core.schema.context import StrawberryContext
from core.schema.mutations.common import UtilityForm
from django import forms
from django.contrib.auth import SESSION_KEY as AUTH_SESSION_KEY
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase
from graphql import GraphQLError

User = get_user_model()


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


def _fake_get_object(model):
    """Build a get_object(info, gid, ...) resolving a relay gid against a model."""

    def get_object(info, global_id, raise_not_found=True, **kwargs):
        _, pk = GlobalIDUtils.from_global_id(global_id)
        obj = model.objects.filter(pk=pk).first()
        if obj is None and raise_not_found:
            raise GraphQLError(f'Object id {model.__name__}:{global_id} not found')
        return obj

    return get_object


def _patch_user_schema_module():
    """Inject the legacy `core.schema.user` module the mutations import at call time."""
    fake_module = types.ModuleType('core.schema.user')
    fake_module.UserType = types.SimpleNamespace(
        get_object=staticmethod(_fake_get_object(User)),
        to_global_id=staticmethod(
            lambda user: GlobalIDUtils.to_global_id('UserType', user.pk)
        ),
    )
    fake_module.SignRequestType = types.SimpleNamespace(
        get_object=staticmethod(_fake_get_object(SignRequest)),
        get_pk=staticmethod(
            lambda gid: GlobalIDUtils.from_global_id(gid)[1]
        ),
    )
    return patch.dict(sys.modules, {'core.schema.user': fake_module})


class UserMutationTestBase(TestCase):
    """Shared setup: org-scoped superuser plus a plain (unprivileged) member."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='UserMutOrg')
        self.user = User.objects.create_superuser(
            username='user_mut_admin',
            email='user_mut_admin@test.com',
            password='testpass',
        )
        self.plain_user = User.objects.create_user(
            username='user_mut_plain',
            email='user_mut_plain@test.com',
            password='testpass',
        )
        for member in (self.user, self.plain_user):
            OrganizationMember.objects.create(
                organization=self.org, member=member, is_active=True,
            )
            member.profile.active_organization = self.org
            member.profile.save()

    def _make_context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.user))

    def _execute(self, mutation, variables=None, context=None):
        with _patch_user_schema_module():
            return schema.execute_sync(
                mutation,
                variable_values=variables,
                context_value=context or self._make_context(),
            )


# ---------------------------------------------------------------------------
# switchUser
# ---------------------------------------------------------------------------

class SwitchUserMutationTest(UserMutationTestBase):
    """Tests for the switchUser (impersonation) mutation."""

    MUTATION = '''
        mutation Switch($id: ID!) {
            switchUser(id: $id) {
                user { username }
            }
        }
    '''

    def test_switch_user_sets_session_keys(self):
        """Switching stores the target in the auth session and remembers the main user."""
        context = self._make_context()
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk)},
            context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['switchUser']['user']['username'], self.plain_user.username,
        )
        session = context.request.session
        self.assertEqual(session[AUTH_SESSION_KEY], self.plain_user.pk)
        self.assertEqual(session['MAIN_USER_PK'], self.user.pk)

    def test_switch_back_with_empty_id_reverts(self):
        """An empty id reverts the session to the remembered main user."""
        context = self._make_context()
        self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk)},
            context,
        )
        result = self._execute(self.MUTATION, {'id': ''}, context)
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['switchUser']['user']['username'], self.user.username,
        )
        self.assertEqual(context.request.session[AUTH_SESSION_KEY], self.user.pk)

    def test_empty_id_without_prior_switch_is_noop(self):
        """An empty id with no prior switch returns the current user unchanged."""
        context = self._make_context()
        result = self._execute(self.MUTATION, {'id': ''}, context)
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['switchUser']['user']['username'], self.user.username,
        )
        self.assertNotIn('MAIN_USER_PK', context.request.session)

    def test_switch_to_unknown_user_errors(self):
        """A gid pointing at a nonexistent user returns an error."""
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', 999999)},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found', str(result.errors[0]))

    # -- permission gate (issue #109) -------------------------------------

    def _grant_switch_permission(self, user):
        """Grant PROFILE_CHANGE_SWITCH_USER via an org-scoped group (house pattern)."""
        permission = Permission.objects.get(
            codename='change_switch_user',
            content_type=ContentType.objects.get_for_model(Profile),
        )
        group = Group.objects.create(name=f'switchers_{user.pk}')
        group.permissions.add(permission)
        self.org.groups.add(group)
        membership = user.memberships.get(organization=self.org)
        membership.groups.add(group)

    def _put_in_switch_group(self, switch_group, *users):
        for user in users:
            user.profile.switch_group = switch_group
            user.profile.save()

    def test_switch_user_anonymous_denied(self):
        """An unauthenticated request is rejected before anything else happens."""
        from django.contrib.auth.models import AnonymousUser
        context = self._make_context(AnonymousUser())
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk)},
            context,
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not authenticated', str(result.errors[0]))
        self.assertNotIn(AUTH_SESSION_KEY, context.request.session)

    def test_switch_user_without_permission_denied(self):
        """An authenticated user without PROFILE_CHANGE_SWITCH_USER is rejected."""
        context = self._make_context(self.plain_user)
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', self.user.pk)},
            context,
        )
        self.assertIsNotNone(result.errors)
        self.assertNotIn(AUTH_SESSION_KEY, context.request.session)
        self.assertNotIn('MAIN_USER_PK', context.request.session)

    def test_switch_user_permitted_and_in_group_succeeds(self):
        """A permitted user switches to a target inside their UserSwitchGroup."""
        from core.models import UserSwitchGroup
        target = User.objects.create_user(
            username='user_mut_target', email='target@test.com', password='x',
        )
        self._grant_switch_permission(self.plain_user)
        self._put_in_switch_group(
            UserSwitchGroup.objects.create(), self.plain_user, target,
        )

        context = self._make_context(self.plain_user)
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', target.pk)},
            context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['switchUser']['user']['username'], target.username,
        )
        session = context.request.session
        self.assertEqual(session[AUTH_SESSION_KEY], target.pk)
        self.assertEqual(session['MAIN_USER_PK'], self.plain_user.pk)

    def test_switch_user_permitted_but_out_of_group_denied(self):
        """A permitted user cannot switch to a target outside their UserSwitchGroup."""
        from core.models import UserSwitchGroup
        target = User.objects.create_user(
            username='user_mut_outsider', email='outsider@test.com', password='x',
        )
        self._grant_switch_permission(self.plain_user)
        self._put_in_switch_group(UserSwitchGroup.objects.create(), self.plain_user)
        self._put_in_switch_group(UserSwitchGroup.objects.create(), target)

        context = self._make_context(self.plain_user)
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', target.pk)},
            context,
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('switch group', str(result.errors[0]))
        self.assertNotIn(AUTH_SESSION_KEY, context.request.session)

    def test_switch_user_permitted_without_any_group_denied(self):
        """Fail closed: permission alone is not enough when no switch group is set."""
        self._grant_switch_permission(self.plain_user)
        context = self._make_context(self.plain_user)
        result = self._execute(
            self.MUTATION,
            {'id': GlobalIDUtils.to_global_id('UserType', self.user.pk)},
            context,
        )
        self.assertIsNotNone(result.errors)
        self.assertNotIn(AUTH_SESSION_KEY, context.request.session)

    def test_switch_user_runs_without_legacy_module_injection(self):
        """switchUser no longer depends on the legacy core.schema.user module."""
        self.assertNotIn('core.schema.user', sys.modules)
        context = self._make_context()
        result = schema.execute_sync(
            self.MUTATION,
            variable_values={
                'id': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk),
            },
            context_value=context,
        )
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['switchUser']['user']['username'], self.plain_user.username,
        )


# ---------------------------------------------------------------------------
# upsertUser
# ---------------------------------------------------------------------------

class _UserUtilityForm(UtilityForm, forms.ModelForm):
    """Minimal UtilityForm registration so apply_forms exercises the full chain."""

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']


class UpsertUserMutationTest(UserMutationTestBase):
    """Tests for the upsertUser mutation (UtilityForm.apply_forms)."""

    # NOTE: UserType.firstName is an async dataloader field — execute_sync
    # cannot resolve it, so only sync fields are selected here.
    MUTATION = '''
        mutation Upsert($input: UserInput!) {
            upsertUser(input: $input) {
                instance { username }
            }
        }
    '''

    def setUp(self):
        super().setUp()
        UtilityForm.register_form(dict, _UserUtilityForm)
        self.addCleanup(UtilityForm.form_map.pop, str(dict), None)

    def test_upsert_updates_current_user(self):
        """The registered form updates the authenticated user's fields."""
        result = self._execute(
            self.MUTATION,
            {'input': {'username': 'renamed_admin', 'firstName': 'Renata'}},
        )
        self.assertIsNone(result.errors)
        self.assertIsNotNone(result.data['upsertUser']['instance'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'renamed_admin')
        self.assertEqual(self.user.first_name, 'Renata')

    def test_upsert_ignores_supplied_id(self):
        """The input id is overridden with the current user; others are untouched."""
        result = self._execute(
            self.MUTATION,
            {'input': {
                'id': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk),
                'username': 'hijack_attempt',
            }},
        )
        self.assertIsNone(result.errors)
        self.plain_user.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.plain_user.username, 'user_mut_plain')
        self.assertEqual(self.user.username, 'hijack_attempt')

    def test_upsert_invalid_username_errors(self):
        """An empty username fails form validation and surfaces as an error."""
        result = self._execute(self.MUTATION, {'input': {'username': ''}})
        self.assertIsNotNone(result.errors)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'user_mut_admin')

    def test_upsert_anonymous_errors(self):
        """An unauthenticated request cannot upsert."""
        from django.contrib.auth.models import AnonymousUser
        result = self._execute(
            self.MUTATION,
            {'input': {'username': 'ghost'}},
            self._make_context(AnonymousUser()),
        )
        self.assertIsNotNone(result.errors)


# ---------------------------------------------------------------------------
# profile
# ---------------------------------------------------------------------------

class ProfileMutationTest(UserMutationTestBase):
    """Tests for the profile mutation (ProfileSerializer, field permissions)."""

    MUTATION = '''
        mutation Prof($input: JSON!) {
            profile(input: $input) {
                ok
                errors { field messages }
            }
        }
    '''

    def test_profile_update_writes_to_draft(self):
        """A non-whitelisted field lands on the draft profile, pending approval."""
        result = self._execute(self.MUTATION, {'input': {'nickname': 'Nicky'}})
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['profile']['ok'])

        original = Profile.objects.get(user=self.user)
        draft = Profile.objects.filter(parent=original).get()
        self.assertEqual(draft.nickname, 'Nicky')
        self.assertNotEqual(original.nickname, 'Nicky')

    def test_profile_permission_denied_for_restricted_field(self):
        """A user without change_nickname permission is rejected."""
        result = self._execute(
            self.MUTATION,
            {'input': {'nickname': 'Sneaky'}},
            self._make_context(self.plain_user),
        )
        self.assertIsNotNone(result.errors)
        draft = Profile.objects.filter(parent__user=self.plain_user).first()
        self.assertIsNone(draft)

    def test_profile_invalid_field_returns_serializer_errors(self):
        """Serializer validation errors come back as MutationResult errors, not exceptions."""
        result = self._execute(
            self.MUTATION, {'input': {'birth_date': 'not-a-date'}},
        )
        self.assertIsNone(result.errors)
        self.assertFalse(result.data['profile']['ok'])
        fields = [e['field'] for e in result.data['profile']['errors']]
        self.assertIn('birth_date', fields)


# ---------------------------------------------------------------------------
# pinUpdate / pinTransaction
# ---------------------------------------------------------------------------

class PinTransactionMutationTest(UserMutationTestBase):
    """Tests for pinUpdate and pinTransaction (PIN verification, proxy user)."""

    PIN_UPDATE = 'mutation Pin($pin: String!) { pinUpdate(pin: $pin) }'
    PIN_TRANSACTION = '''
        mutation PinTx($pin: String!, $proxy: ID) {
            pinTransaction(pin: $pin, proxyUser: $proxy)
        }
    '''

    def test_pin_update_sets_pin(self):
        """pinUpdate hashes and stores the PIN and logs a CHANGED transaction."""
        result = self._execute(self.PIN_UPDATE, {'pin': '2468'})
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['pinUpdate'])
        self.user.profile.refresh_from_db()
        self.assertTrue(self.user.profile.has_pin())
        self.assertTrue(PinTransaction.objects.filter(
            user=self.user, kind=PinTransactionKindChoices.CHANGED,
        ).exists())

    def test_pin_transaction_valid_pin(self):
        """A correct PIN authenticates and records an AUTHENTICATED transaction."""
        self.user.profile.update_pin('2468')
        result = self._execute(self.PIN_TRANSACTION, {'pin': '2468'})
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['pinTransaction'])
        self.assertIsNotNone(PinTransaction.objects.active_authentication(self.user))

    def test_pin_transaction_invalid_pin_errors(self):
        """A wrong PIN raises and records a FAIL transaction."""
        self.user.profile.update_pin('2468')
        result = self._execute(self.PIN_TRANSACTION, {'pin': '0000'})
        self.assertIsNotNone(result.errors)
        self.assertIn('Invalid pin', str(result.errors[0]))
        self.assertTrue(PinTransaction.objects.filter(
            user=self.user, kind=PinTransactionKindChoices.FAIL,
        ).exists())

    def test_pin_transaction_without_pin_set_errors(self):
        """Authenticating before any PIN is set raises."""
        result = self._execute(self.PIN_TRANSACTION, {'pin': '2468'})
        self.assertIsNotNone(result.errors)
        self.assertIn('Pin not set', str(result.errors[0]))

    def test_pin_transaction_with_proxy_user(self):
        """The proxy user's PIN is verified; the transaction records both users."""
        self.plain_user.profile.update_pin('1357')
        result = self._execute(
            self.PIN_TRANSACTION,
            {'pin': '1357',
             'proxy': GlobalIDUtils.to_global_id('UserType', self.plain_user.pk)},
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['pinTransaction'])
        transaction = PinTransaction.objects.filter(
            kind=PinTransactionKindChoices.AUTHENTICATED,
        ).get()
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.proxy_user, self.plain_user)


# ---------------------------------------------------------------------------
# signRequest mutations
# ---------------------------------------------------------------------------

class _FakeSignTarget(SignRequestMixin):
    """Stand-in for a domain object living behind SignRequest.global_id_link."""

    def __init__(self, allowed_users):
        self._allowed_users = allowed_users

    def users_allowed_to_sign(self):
        return self._allowed_users


class SignRequestMutationTest(UserMutationTestBase):
    """Tests for signRequestUser / signRequestSign / signRequestCancel."""

    REQUEST = '''
        mutation Req($gid: String!, $user: ID!) {
            signRequestUser(gid: $gid, userToRequest: $user)
        }
    '''
    SIGN = 'mutation Sign($gid: String!) { signRequestSign(gid: $gid) }'
    CANCEL = '''
        mutation Cancel($gid: String!, $note: String!) {
            signRequestCancel(gid: $gid, note: $note)
        }
    '''

    def setUp(self):
        super().setUp()
        sign_request_ct = ContentType.objects.get_for_model(SignRequest)
        signers = Group.objects.create(name='signers')
        signers.permissions.add(
            Permission.objects.get(codename='change_sign', content_type=sign_request_ct),
        )
        self.signer = User.objects.create_user(
            username='sign_mut_signer', email='signer@test.com', password='x',
        )
        self.signer.groups.add(signers)

        self.requester = self.plain_user
        self.link = GlobalIDLink.objects.create(
            app_label='core',
            gid=GlobalIDUtils.to_global_id('SignRequestType', 424242),
            name='fake-sign-target',
        )
        self.sign_request = SignRequest.objects.create(
            user=self.requester,
            status=SignRequestStatusChoices.SIGN_REQUIRED,
            global_id_link=self.link,
            created_by=self.requester,
        )
        self.sr_gid = self.sign_request.global_id

        target = _FakeSignTarget(User.objects.filter(pk=self.signer.pk))
        get_instance_patcher = patch.object(
            GlobalIDLink, 'get_instance', return_value=target,
        )
        get_instance_patcher.start()
        self.addCleanup(get_instance_patcher.stop)

    def test_request_user_adds_signer(self):
        """Requesting a sign from a permitted user records them on the request."""
        result = self._execute(
            self.REQUEST,
            {'gid': self.sr_gid,
             'user': GlobalIDUtils.to_global_id('UserType', self.signer.pk)},
            self._make_context(self.requester),
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['signRequestUser'])
        self.assertIn(self.signer, self.sign_request.sign_requested.all())

    def test_request_user_without_sign_permission_errors(self):
        """Requesting a sign from a user lacking change_sign is denied."""
        no_perm = User.objects.create_user(
            username='sign_mut_noperm', email='noperm@test.com', password='x',
        )
        result = self._execute(
            self.REQUEST,
            {'gid': self.sr_gid,
             'user': GlobalIDUtils.to_global_id('UserType', no_perm.pk)},
            self._make_context(self.requester),
        )
        self.assertIsNotNone(result.errors)
        self.assertNotIn(no_perm, self.sign_request.sign_requested.all())

    def test_request_user_unknown_sign_request_errors(self):
        """A gid pointing at a nonexistent sign request errors out."""
        result = self._execute(
            self.REQUEST,
            {'gid': GlobalIDUtils.to_global_id('SignRequestType', 999999),
             'user': GlobalIDUtils.to_global_id('UserType', self.signer.pk)},
            self._make_context(self.requester),
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found', str(result.errors[0]))

    def _authenticate_signer_pin(self):
        self.signer.profile.update_pin('9999')
        self.signer.profile.authenticate('9999')

    def test_sign_with_active_pin_transaction(self):
        """A requested signer with an active PIN transaction completes the request."""
        self.sign_request.sign_requested.add(self.signer)
        self._authenticate_signer_pin()
        result = self._execute(
            self.SIGN, {'gid': self.sr_gid}, self._make_context(self.signer),
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['signRequestSign'])
        self.sign_request.refresh_from_db()
        self.assertEqual(self.sign_request.status, SignRequestStatusChoices.SIGNED)
        self.assertIsNotNone(self.sign_request.signed_at)

    def test_sign_without_pin_transaction_errors(self):
        """Signing without an active PIN transaction is rejected."""
        self.sign_request.sign_requested.add(self.signer)
        result = self._execute(
            self.SIGN, {'gid': self.sr_gid}, self._make_context(self.signer),
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('no active pin transaction', str(result.errors[0]))
        self.sign_request.refresh_from_db()
        self.assertEqual(self.sign_request.status, SignRequestStatusChoices.SIGN_REQUIRED)

    def test_sign_without_permission_errors(self):
        """A user without change_sign cannot sign."""
        result = self._execute(
            self.SIGN, {'gid': self.sr_gid}, self._make_context(self.requester),
        )
        self.assertIsNotNone(result.errors)
        self.sign_request.refresh_from_db()
        self.assertEqual(self.sign_request.status, SignRequestStatusChoices.SIGN_REQUIRED)

    def test_cancel_sets_status_and_note(self):
        """A privileged user can cancel; status, canceller and note are recorded."""
        result = self._execute(
            self.CANCEL, {'gid': self.sr_gid, 'note': 'no longer needed'},
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['signRequestCancel'])
        self.sign_request.refresh_from_db()
        self.assertEqual(self.sign_request.status, SignRequestStatusChoices.CANCELED)
        self.assertEqual(self.sign_request.cancel_by, self.user)
        self.assertEqual(self.sign_request.note, 'no longer needed')

    def test_cancel_without_permission_errors(self):
        """A user without change_cancel cannot cancel."""
        result = self._execute(
            self.CANCEL,
            {'gid': self.sr_gid, 'note': 'nope'},
            self._make_context(self.signer),
        )
        self.assertIsNotNone(result.errors)
        self.sign_request.refresh_from_db()
        self.assertEqual(self.sign_request.status, SignRequestStatusChoices.SIGN_REQUIRED)

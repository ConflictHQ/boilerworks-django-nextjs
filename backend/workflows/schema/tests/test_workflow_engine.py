"""Workflow engine integration tests (issue #68).

Exercises the full engine through the assembled GraphQL schema: start,
transition (with condition evaluation), admin override, plus model-level
coverage of every condition type and eager (Celery ALWAYS_EAGER) execution
of every action type.
"""
from unittest.mock import patch

from config.schema import schema
from core.models import Link, Notification
from core.models.upload import FileUpload
from core.schema.context import StrawberryContext
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sessions.backends.db import SessionStore
from django.core import mail
from django.test import TestCase
from workflows.models import WorkflowDefinition, WorkflowInstance

User = get_user_model()

STATES = [
    {'name': 'draft', 'label': 'Draft', 'is_initial': True},
    {'name': 'review', 'label': 'In Review'},
    {'name': 'approved', 'label': 'Approved', 'is_final': True},
    {'name': 'rejected', 'label': 'Rejected', 'is_final': True},
]

TRANSITIONS = [
    {
        'from_state': 'draft', 'to_state': 'review', 'label': 'Submit',
        'conditions': [{'type': 'is_authenticated'}],
        'actions': [],
    },
    {
        'from_state': 'review', 'to_state': 'approved', 'label': 'Approve',
        'conditions': [{'type': 'user_has_role', 'role': 'approvers'}],
        'actions': [],
    },
    {
        'from_state': 'review', 'to_state': 'rejected', 'label': 'Reject',
        'conditions': [],
        'actions': [],
    },
]


class FakeRequest:
    """Minimal request mock for StrawberryContext."""

    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class WorkflowEngineTestBase(TestCase):
    """Shared setup: org-scoped superuser, plain user, workflow + tracked Link."""

    def setUp(self):
        from organization.models import Organization, OrganizationMember

        self.org = Organization.objects.create(name='WorkflowOrg')
        self.user = User.objects.create_superuser(
            username='wf_admin', email='wf_admin@test.com', password='testpass',
        )
        self.plain_user = User.objects.create_user(
            username='wf_plain', email='wf_plain@test.com', password='testpass',
        )
        for member in (self.user, self.plain_user):
            OrganizationMember.objects.create(
                organization=self.org, member=member, is_active=True,
            )
            member.profile.active_organization = self.org
            member.profile.save()

        self.workflow = WorkflowDefinition.objects.create(
            name='Doc Review',
            slug='doc-review',
            model_label='core.Link',
            states=STATES,
            transitions=TRANSITIONS,
            is_enabled=True,
            created_by=self.user,
        )
        self.link = Link.objects.create(
            url='https://example.test/doc',
            title='Doc',
            created_by=self.plain_user,
        )

    def _make_context(self, user=None):
        return StrawberryContext(FakeRequest(user or self.user))

    def _execute(self, query, variables=None, user=None):
        return schema.execute_sync(
            query,
            variable_values=variables,
            context_value=self._make_context(user),
        )

    def _start_instance(self, obj=None, user=None):
        return WorkflowInstance.start(self.workflow, obj or self.link, user or self.user)


# ---------------------------------------------------------------------------
# startWorkflow
# ---------------------------------------------------------------------------

class StartWorkflowMutationTest(WorkflowEngineTestBase):
    """Tests for the startWorkflow mutation."""

    MUTATION = '''
        mutation Start($slug: String!, $model: String!, $objectId: Int!) {
            startWorkflow(workflowSlug: $slug, modelLabel: $model, objectId: $objectId) {
                ok
                instanceId
            }
        }
    '''

    def test_start_valid(self):
        """A valid start creates an instance in the initial state with a start log."""
        result = self._execute(
            self.MUTATION,
            {'slug': 'doc-review', 'model': 'core.Link', 'objectId': self.link.pk},
        )
        self.assertIsNone(result.errors)
        data = result.data['startWorkflow']
        self.assertTrue(data['ok'])

        instance = WorkflowInstance.objects.get(pk=data['instanceId'])
        self.assertEqual(instance.current_state, 'draft')
        self.assertEqual(instance.content_object, self.link)
        self.assertIsNone(instance.completed_at)

        log = instance.transition_logs.get()
        self.assertEqual(log.from_state, '')
        self.assertEqual(log.to_state, 'draft')
        self.assertEqual(log.note, 'Workflow started')

    def test_start_invalid_model_errors(self):
        """A bogus model label errors out and creates nothing."""
        result = self._execute(
            self.MUTATION,
            {'slug': 'doc-review', 'model': 'core.NoSuchModel', 'objectId': 1},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('Object not found', str(result.errors[0]))
        self.assertEqual(WorkflowInstance.objects.count(), 0)

    def test_start_unknown_object_errors(self):
        """An object id that does not exist errors out."""
        result = self._execute(
            self.MUTATION,
            {'slug': 'doc-review', 'model': 'core.Link', 'objectId': 999999},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('Object not found', str(result.errors[0]))

    def test_start_disabled_workflow_errors(self):
        """A disabled workflow cannot be started."""
        self.workflow.is_enabled = False
        self.workflow.save()
        result = self._execute(
            self.MUTATION,
            {'slug': 'doc-review', 'model': 'core.Link', 'objectId': self.link.pk},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found or disabled', str(result.errors[0]))

    def test_start_unknown_slug_errors(self):
        """An unknown workflow slug errors out."""
        result = self._execute(
            self.MUTATION,
            {'slug': 'no-such-flow', 'model': 'core.Link', 'objectId': self.link.pk},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found or disabled', str(result.errors[0]))

    def test_start_without_initial_state_errors(self):
        """A workflow whose states lack an initial marker cannot start instances."""
        self.workflow.states = []
        self.workflow.save()
        result = self._execute(
            self.MUTATION,
            {'slug': 'doc-review', 'model': 'core.Link', 'objectId': self.link.pk},
        )
        self.assertIsNotNone(result.errors)
        self.assertEqual(WorkflowInstance.objects.count(), 0)


# ---------------------------------------------------------------------------
# transitionWorkflow
# ---------------------------------------------------------------------------

class TransitionWorkflowMutationTest(WorkflowEngineTestBase):
    """Tests for the transitionWorkflow mutation."""

    MUTATION = '''
        mutation Trans($id: ID!, $to: String!, $note: String!) {
            transitionWorkflow(instanceId: $id, toState: $to, note: $note) {
                ok
            }
        }
    '''

    def _transition(self, instance, to_state, user=None, note=''):
        return self._execute(
            self.MUTATION,
            {'id': str(instance.pk), 'to': to_state, 'note': note},
            user=user,
        )

    def test_valid_transition(self):
        """A defined transition with met conditions moves the state and logs it."""
        instance = self._start_instance()
        result = self._transition(instance, 'review', note='sending for review')
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['transitionWorkflow']['ok'])

        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'review')
        log = instance.transition_logs.first()  # newest first
        self.assertEqual((log.from_state, log.to_state), ('draft', 'review'))
        self.assertEqual(log.note, 'sending for review')
        self.assertEqual(log.transitioned_by, self.user)

    def test_undefined_transition_rejected(self):
        """A transition that is not defined for the current state is rejected."""
        instance = self._start_instance()
        result = self._transition(instance, 'approved')
        self.assertIsNotNone(result.errors)
        self.assertIn('No transition', str(result.errors[0]))
        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'draft')

    def test_condition_not_met_rejected(self):
        """user_has_role blocks users outside the role group."""
        instance = self._start_instance()
        self._transition(instance, 'review', user=self.plain_user)
        result = self._transition(instance, 'approved', user=self.plain_user)
        self.assertIsNotNone(result.errors)
        self.assertIn('Condition not met: user_has_role', str(result.errors[0]))
        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'review')

    def test_condition_met_via_role_and_final_state_completes(self):
        """A user in the required group can approve; final state completes the workflow."""
        approvers = Group.objects.create(name='approvers')
        self.plain_user.groups.add(approvers)

        instance = self._start_instance()
        self._transition(instance, 'review', user=self.plain_user)
        result = self._transition(instance, 'approved', user=self.plain_user)
        self.assertIsNone(result.errors)

        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'approved')
        self.assertIsNotNone(instance.completed_at)
        self.assertTrue(instance.is_completed)

    def test_completed_workflow_rejects_transitions(self):
        """No further transitions are accepted once the workflow completed."""
        instance = self._start_instance()
        self._transition(instance, 'review')
        self._transition(instance, 'approved')  # superuser passes user_has_role
        instance.refresh_from_db()
        self.assertTrue(instance.is_completed)

        result = self._transition(instance, 'rejected')
        self.assertIsNotNone(result.errors)
        self.assertIn('already completed', str(result.errors[0]))

    def test_unknown_instance_errors(self):
        """A nonexistent instance id errors out."""
        result = self._execute(
            self.MUTATION, {'id': '999999', 'to': 'review', 'note': ''},
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('not found', str(result.errors[0]))

    def test_history_records_full_chain(self):
        """The transition log records the complete ordered history."""
        instance = self._start_instance()
        self._transition(instance, 'review')
        self._transition(instance, 'rejected')

        logs = list(instance.transition_logs.all())  # ordering: newest first
        self.assertEqual(len(logs), 3)
        self.assertEqual(
            [(log.from_state, log.to_state) for log in reversed(logs)],
            [('', 'draft'), ('draft', 'review'), ('review', 'rejected')],
        )


# ---------------------------------------------------------------------------
# Condition evaluation (model level)
# ---------------------------------------------------------------------------

class ConditionEvaluationTest(WorkflowEngineTestBase):
    """Direct coverage of every condition type."""

    def setUp(self):
        super().setUp()
        self.instance = self._start_instance()

    def test_user_has_role(self):
        cond = {'type': 'user_has_role', 'role': 'editors'}
        self.assertFalse(self.instance._evaluate_condition(cond, self.plain_user))
        self.plain_user.groups.add(Group.objects.create(name='editors'))
        self.assertTrue(self.instance._evaluate_condition(cond, self.plain_user))
        # Superusers bypass role checks; missing user fails closed.
        self.assertTrue(self.instance._evaluate_condition(cond, self.user))
        self.assertFalse(self.instance._evaluate_condition(cond, None))

    def test_field_equals(self):
        cond = {'type': 'field_equals', 'field': 'title', 'value': 'Doc'}
        self.assertTrue(self.instance._evaluate_condition(cond, self.user))
        cond['value'] = 'Other'
        self.assertFalse(self.instance._evaluate_condition(cond, self.user))

    def test_field_in(self):
        cond = {'type': 'field_in', 'field': 'title', 'values': ['Doc', 'Memo']}
        self.assertTrue(self.instance._evaluate_condition(cond, self.user))
        cond['values'] = ['Memo']
        self.assertFalse(self.instance._evaluate_condition(cond, self.user))

    def test_is_authenticated(self):
        from django.contrib.auth.models import AnonymousUser
        cond = {'type': 'is_authenticated'}
        self.assertTrue(self.instance._evaluate_condition(cond, self.plain_user))
        self.assertFalse(self.instance._evaluate_condition(cond, AnonymousUser()))
        self.assertFalse(self.instance._evaluate_condition(cond, None))

    def test_is_superuser(self):
        cond = {'type': 'is_superuser'}
        self.assertTrue(self.instance._evaluate_condition(cond, self.user))
        self.assertFalse(self.instance._evaluate_condition(cond, self.plain_user))

    def test_unknown_condition_passes_open(self):
        """Unknown condition types are logged and pass (documented behavior)."""
        self.assertTrue(
            self.instance._evaluate_condition({'type': 'no_such_check'}, None),
        )

    def test_get_available_transitions_reports_conditions(self):
        available = self.instance.get_available_transitions(self.plain_user)
        self.assertEqual([t['to_state'] for t in available], ['review'])
        self.assertTrue(available[0]['conditions_met'])


# ---------------------------------------------------------------------------
# Action execution (Celery eager in Tests configuration)
# ---------------------------------------------------------------------------

class ActionExecutionTest(WorkflowEngineTestBase):
    """Each action type executes on transition (CELERY_TASK_ALWAYS_EAGER)."""

    def _workflow_with_actions(self, actions):
        self.workflow.transitions = [{
            'from_state': 'draft', 'to_state': 'review', 'label': 'Submit',
            'conditions': [],
            'actions': actions,
        }]
        self.workflow.save()
        return self._start_instance()

    def test_notify_user_creates_notification(self):
        instance = self._workflow_with_actions([{
            'type': 'notify_user', 'user': 'form_owner',
            'subject': 'Review please', 'message': 'A doc awaits review',
        }])
        instance.transition('review', self.user)

        notification = Notification.objects.get(user=self.link.created_by)
        self.assertEqual(notification.subject, 'Review please')
        self.assertEqual(notification.message, 'A doc awaits review')

    def test_send_email_uses_owner_address(self):
        instance = self._workflow_with_actions([{
            'type': 'send_email', 'to': 'form_owner', 'subject': 'Doc moved',
        }])
        instance.transition('review', self.user)

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Doc moved')
        self.assertEqual(mail.outbox[0].to, [self.plain_user.email])

    def test_call_webhook_posts_payload(self):
        instance = self._workflow_with_actions([{
            'type': 'call_webhook', 'url': 'https://hooks.test/wf',
        }])
        with patch('workflows.tasks.requests.post') as mock_post:
            instance.transition('review', self.user)

        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], 'https://hooks.test/wf')
        payload = kwargs['json']
        self.assertEqual(payload['from_state'], 'draft')
        self.assertEqual(payload['to_state'], 'review')
        self.assertEqual(payload['object_id'], self.link.pk)
        self.assertEqual(payload['user'], self.user.username)

    def test_update_field_mutates_tracked_object(self):
        instance = self._workflow_with_actions([{
            'type': 'update_field', 'field': 'title', 'value': 'In Review',
        }])
        instance.transition('review', self.user)

        self.link.refresh_from_db()
        self.assertEqual(self.link.title, 'In Review')

    def test_current_user_recipient_resolution(self):
        instance = self._workflow_with_actions([{
            'type': 'notify_user', 'user': 'current_user',
        }])
        instance.transition('review', self.user)
        self.assertTrue(Notification.objects.filter(user=self.user).exists())


# ---------------------------------------------------------------------------
# overrideWorkflowState
# ---------------------------------------------------------------------------

class OverrideWorkflowMutationTest(WorkflowEngineTestBase):
    """Tests for the admin override mutation."""

    MUTATION = '''
        mutation Override($id: ID!, $to: String!, $note: String!) {
            overrideWorkflowState(instanceId: $id, toState: $to, note: $note) {
                ok
            }
        }
    '''

    def test_superuser_override_creates_log(self):
        """A superuser can force any state; the log is marked as an override."""
        instance = self._start_instance()
        result = self._execute(
            self.MUTATION,
            {'id': str(instance.pk), 'to': 'approved', 'note': 'unblocking'},
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['overrideWorkflowState']['ok'])

        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'approved')
        log = instance.transition_logs.first()
        self.assertEqual(log.note, '[ADMIN OVERRIDE] unblocking')
        self.assertEqual(log.transitioned_by, self.user)

    def test_non_superuser_override_denied(self):
        """Non-superusers cannot override, even for defined transitions."""
        instance = self._start_instance()
        result = self._execute(
            self.MUTATION,
            {'id': str(instance.pk), 'to': 'review', 'note': ''},
            user=self.plain_user,
        )
        self.assertIsNotNone(result.errors)
        self.assertIn('Only superusers', str(result.errors[0]))
        instance.refresh_from_db()
        self.assertEqual(instance.current_state, 'draft')


# ---------------------------------------------------------------------------
# GenericForeignKey across models
# ---------------------------------------------------------------------------

class GenericForeignKeyTest(WorkflowEngineTestBase):
    """The engine tracks objects of different models via GenericForeignKey."""

    def test_instances_attach_to_different_models(self):
        upload_workflow = WorkflowDefinition.objects.create(
            name='Upload Flow',
            slug='upload-flow',
            model_label='core.FileUpload',
            states=STATES,
            transitions=TRANSITIONS,
            is_enabled=True,
            created_by=self.user,
        )
        file_upload = FileUpload.objects.create(created_by=self.user)

        link_instance = self._start_instance()
        upload_instance = WorkflowInstance.start(upload_workflow, file_upload, self.user)

        self.assertEqual(link_instance.content_object, self.link)
        self.assertEqual(upload_instance.content_object, file_upload)
        self.assertNotEqual(
            link_instance.content_type, upload_instance.content_type,
        )

        # Both progress independently through the same state graph.
        upload_instance.transition('review', self.user)
        upload_instance.refresh_from_db()
        link_instance.refresh_from_db()
        self.assertEqual(upload_instance.current_state, 'review')
        self.assertEqual(link_instance.current_state, 'draft')

    def test_workflow_instances_query_filters_by_model(self):
        """The workflowInstances query scopes by object id and model label."""
        link_instance = self._start_instance()
        result = self._execute(
            '''
            query Instances($objectId: Int!, $model: String) {
                workflowInstances(objectId: $objectId, modelLabel: $model) {
                    currentState
                }
            }
            ''',
            {'objectId': self.link.pk, 'model': 'core.Link'},
        )
        self.assertIsNone(result.errors)
        self.assertEqual(
            result.data['workflowInstances'],
            [{'currentState': link_instance.current_state}],
        )

"""Workflow Engine models.

WorkflowDefinition: DB-configurable state machine (states, transitions, conditions, actions).
WorkflowInstance: tracks a specific object through a workflow.
TransitionLog: immutable history of every state change.
"""
import logging
from typing import Optional

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import BaseCoreModel, Tracking

logger = logging.getLogger(__name__)


class WorkflowDefinition(BaseCoreModel):
    """A reusable workflow definition with states and transitions.

    States and transitions are stored as JSON, making workflows
    configurable without Python code.

    State format:
        [{"name": "draft", "label": "Draft", "is_initial": true, "is_final": false, "color": "#6b7280"}]

    Transition format:
        [{"from_state": "draft", "to_state": "submitted", "label": "Submit",
          "conditions": [{"type": "user_has_role", "role": "submitter"}],
          "actions": [{"type": "notify_user", "user": "form_owner"}],
          "timeout_hours": null}]
    """
    model_label = models.CharField(
        max_length=100,
        help_text='Django model this workflow applies to (e.g. "forms.FormSubmission")',
        db_index=True,
    )
    states = models.JSONField(
        default=list,
        help_text='List of state definitions [{name, label, is_initial, is_final, color}]',
    )
    transitions = models.JSONField(
        default=list,
        help_text='List of transition definitions [{from_state, to_state, label, conditions, actions, timeout_hours}]',
    )
    is_enabled = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['slug', 'model_label'], name='unique_workflow_per_model'),
        ]

    def get_initial_state(self) -> Optional[str]:
        for state in self.states:
            if state.get('is_initial'):
                return state['name']
        return self.states[0]['name'] if self.states else None

    def get_final_states(self) -> set[str]:
        return {s['name'] for s in self.states if s.get('is_final')}

    def get_state_label(self, state_name: str) -> str:
        for s in self.states:
            if s['name'] == state_name:
                return s.get('label', state_name)
        return state_name

    def get_available_transitions(self, from_state: str) -> list[dict]:
        return [t for t in self.transitions if t['from_state'] == from_state]

    def get_transition(self, from_state: str, to_state: str) -> Optional[dict]:
        for t in self.transitions:
            if t['from_state'] == from_state and t['to_state'] == to_state:
                return t
        return None

    def validate_definition(self) -> list[str]:
        """Validate the workflow definition for correctness."""
        errors = []
        state_names = {s['name'] for s in self.states}
        initial_count = sum(1 for s in self.states if s.get('is_initial'))

        if not self.states:
            errors.append('Workflow must have at least one state')
        if initial_count != 1:
            errors.append(f'Workflow must have exactly one initial state (found {initial_count})')

        for t in self.transitions:
            if t['from_state'] not in state_names:
                errors.append(f'Transition from unknown state: {t["from_state"]}')
            if t['to_state'] not in state_names:
                errors.append(f'Transition to unknown state: {t["to_state"]}')

        return errors

    def __str__(self):
        return f'{self.name} ({self.model_label})'


class WorkflowInstance(Tracking):
    """Tracks a specific object through a workflow.

    Uses GenericForeignKey to attach to any Django model.
    """
    workflow = models.ForeignKey(
        WorkflowDefinition,
        on_delete=models.PROTECT,
        related_name='instances',
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    current_state = models.CharField(max_length=100, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Temporal integration (future)
    temporal_workflow_id = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['workflow', 'current_state']),
        ]

    @classmethod
    def start(cls, workflow: WorkflowDefinition, obj, user=None) -> 'WorkflowInstance':
        """Start a new workflow instance for an object."""
        initial_state = workflow.get_initial_state()
        if not initial_state:
            raise ValidationError('Workflow has no initial state')

        ct = ContentType.objects.get_for_model(obj)
        instance = cls.objects.create(
            workflow=workflow,
            content_type=ct,
            object_id=obj.pk,
            current_state=initial_state,
            created_by=user,
            updated_by=user,
        )

        TransitionLog.objects.create(
            instance=instance,
            from_state='',
            to_state=initial_state,
            transitioned_by=user,
            note='Workflow started',
        )

        return instance

    def transition(self, to_state: str, user=None, note: str = '') -> 'TransitionLog':
        """Execute a state transition.

        Validates the transition exists and evaluates conditions.
        Fires actions after successful transition.
        """
        transition_def = self.workflow.get_transition(self.current_state, to_state)
        if not transition_def:
            raise ValidationError(
                f'No transition from "{self.current_state}" to "{to_state}" '
                f'in workflow "{self.workflow.name}"'
            )

        # Evaluate conditions
        conditions = transition_def.get('conditions', [])
        for condition in conditions:
            if not self._evaluate_condition(condition, user):
                raise ValidationError(
                    f'Condition not met: {condition.get("type", "unknown")}'
                )

        # Execute transition
        from_state = self.current_state
        self.current_state = to_state
        self.updated_by = user

        # Check if final state
        if to_state in self.workflow.get_final_states():
            self.completed_at = timezone.now()

        self.save()

        # Log
        log = TransitionLog.objects.create(
            instance=self,
            from_state=from_state,
            to_state=to_state,
            transitioned_by=user,
            note=note or transition_def.get('label', ''),
        )

        # Fire actions asynchronously
        actions = transition_def.get('actions', [])
        for action in actions:
            self._fire_action(action, from_state, to_state, user)

        return log

    def get_available_transitions(self, user=None) -> list[dict]:
        """Get transitions available from the current state."""
        transitions = self.workflow.get_available_transitions(self.current_state)
        available = []
        for t in transitions:
            # Check conditions
            conditions_met = all(
                self._evaluate_condition(c, user)
                for c in t.get('conditions', [])
            )
            available.append({
                **t,
                'conditions_met': conditions_met,
            })
        return available

    @property
    def is_completed(self) -> bool:
        return self.completed_at is not None

    def _evaluate_condition(self, condition: dict, user) -> bool:
        """Evaluate a transition condition."""
        ctype = condition.get('type', '')

        if ctype == 'user_has_role':
            if not user:
                return False
            role = condition.get('role', '')
            return user.groups.filter(name=role).exists() or user.is_superuser

        if ctype == 'field_equals':
            obj = self.content_object
            field = condition.get('field', '')
            value = condition.get('value')
            return getattr(obj, field, None) == value

        if ctype == 'field_in':
            obj = self.content_object
            field = condition.get('field', '')
            values = condition.get('values', [])
            return getattr(obj, field, None) in values

        if ctype == 'is_authenticated':
            return user and user.is_authenticated

        if ctype == 'is_superuser':
            return user and user.is_superuser

        # Unknown condition type — pass by default
        logger.warning(f'Unknown condition type: {ctype}')
        return True

    def _fire_action(self, action: dict, from_state: str, to_state: str, user):
        """Fire a transition action asynchronously via Celery."""
        try:
            from workflows.tasks import execute_workflow_action
            execute_workflow_action.delay(
                instance_id=self.pk,
                action=action,
                from_state=from_state,
                to_state=to_state,
                user_id=user.pk if user else None,
            )
        except Exception as e:
            logger.warning(f'Failed to fire action {action}: {e}')

    def __str__(self):
        return f'{self.workflow.name}: {self.current_state} (obj={self.object_id})'


class TransitionLog(models.Model):
    """Immutable log of every state transition."""
    instance = models.ForeignKey(
        WorkflowInstance,
        on_delete=models.CASCADE,
        related_name='transition_logs',
    )
    from_state = models.CharField(max_length=100)
    to_state = models.CharField(max_length=100)
    transitioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
    )
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.from_state} → {self.to_state} at {self.timestamp}'

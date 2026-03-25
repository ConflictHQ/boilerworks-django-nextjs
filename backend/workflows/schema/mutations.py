from __future__ import annotations

from typing import Optional

import strawberry
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from strawberry.types import Info

from core.schema.common import MutationResult
from core.schema.common import ValidationError as GQLValidationError
from workflows.models import WorkflowDefinition, WorkflowInstance


@strawberry.type
class StartWorkflowResult(MutationResult):
    instance_id: Optional[strawberry.ID] = None


def _require_staff(user):
    """Raise GraphQLError if user is not authenticated staff/superuser."""
    if not user or not user.is_authenticated:
        raise GraphQLError('Authentication required')
    if not (user.is_staff or user.is_superuser):
        raise GraphQLError('Staff or superuser access required')


@strawberry.type
class Mutation:

    @strawberry.mutation(description="Start a workflow for an object.")
    def start_workflow(
        self, info: Info, workflow_slug: str, model_label: str, object_id: int,
    ) -> StartWorkflowResult:
        user = info.context.user
        workflow = WorkflowDefinition.objects.filter(slug=workflow_slug, is_enabled=True).first()
        if not workflow:
            raise GraphQLError(f'Workflow "{workflow_slug}" not found or disabled')

        # Resolve the model
        try:
            parts = model_label.split('.')
            model = apps.get_model(parts[0], parts[-1])
            obj = model.objects.get(pk=object_id)
        except Exception as e:
            raise GraphQLError(f'Object not found: {model_label}:{object_id} — {e}')

        try:
            instance = WorkflowInstance.start(workflow, obj, user)
            return StartWorkflowResult(ok=True, instance_id=str(instance.pk))
        except ValidationError as e:
            raise GraphQLError(str(e))

    @strawberry.mutation(description="Transition a workflow instance to a new state.")
    def transition_workflow(
        self, info: Info, instance_id: strawberry.ID, to_state: str, note: str = '',
    ) -> MutationResult:
        user = info.context.user
        instance = WorkflowInstance.objects.filter(pk=instance_id).first()
        if not instance:
            raise GraphQLError(f'Workflow instance {instance_id} not found')

        if instance.is_completed:
            raise GraphQLError('Workflow is already completed')

        try:
            instance.transition(to_state, user, note)
            return MutationResult.success()
        except ValidationError as e:
            raise GraphQLError(str(e))

    @strawberry.mutation(description="Force a workflow instance to a specific state (admin override).")
    def override_workflow_state(
        self, info: Info, instance_id: strawberry.ID, to_state: str, note: str = '',
    ) -> MutationResult:
        user = info.context.user
        if not user.is_superuser:
            raise GraphQLError('Only superusers can override workflow state')

        instance = WorkflowInstance.objects.filter(pk=instance_id).first()
        if not instance:
            raise GraphQLError(f'Workflow instance {instance_id} not found')

        from workflows.models import TransitionLog
        from_state = instance.current_state
        instance.current_state = to_state
        instance.updated_by = user
        instance.save()

        TransitionLog.objects.create(
            instance=instance,
            from_state=from_state,
            to_state=to_state,
            transitioned_by=user,
            note=f'[ADMIN OVERRIDE] {note}',
        )

        return MutationResult.success()

    @strawberry.mutation(description="Create a new workflow definition (staff only).")
    def create_workflow_definition(
        self, info: Info,
        name: str,
        slug: str,
        model_label: str,
        states: strawberry.scalars.JSON,
        transitions: strawberry.scalars.JSON,
        description: Optional[str] = None,
        is_enabled: bool = False,
    ) -> MutationResult:
        user = info.context.user
        _require_staff(user)

        workflow = WorkflowDefinition(
            name=name,
            slug=slug,
            model_label=model_label,
            states=states,
            transitions=transitions,
            description=description or '',
            is_enabled=is_enabled,
            created_by=user,
            updated_by=user,
        )

        # Only validate if states are provided — empty workflows are valid
        # during creation (user will add states in the builder)
        if states:
            errors = workflow.validate_definition()
            if errors:
                return MutationResult(
                    ok=False,
                    errors=[GQLValidationError(field='definition', messages=errors)],
                )

        try:
            workflow.save()
        except Exception as e:
            raise GraphQLError(f'Failed to create workflow definition: {e}')

        return MutationResult.success()

    @strawberry.mutation(description="Update an existing workflow definition (staff only).")
    def update_workflow_definition(
        self, info: Info,
        slug: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        model_label: Optional[str] = None,
        states: Optional[strawberry.scalars.JSON] = None,
        transitions: Optional[strawberry.scalars.JSON] = None,
        is_enabled: Optional[bool] = None,
    ) -> MutationResult:
        user = info.context.user
        _require_staff(user)

        workflow = WorkflowDefinition.objects.filter(slug=slug).first()
        if not workflow:
            raise GraphQLError(f'Workflow definition "{slug}" not found')

        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if model_label is not None:
            workflow.model_label = model_label
        if states is not None:
            workflow.states = states
        if transitions is not None:
            workflow.transitions = transitions
        if is_enabled is not None:
            workflow.is_enabled = is_enabled

        workflow.updated_by = user

        errors = workflow.validate_definition()
        if errors:
            return MutationResult(
                ok=False,
                errors=[GQLValidationError(field='definition', messages=errors)],
            )

        try:
            workflow.save()
        except Exception as e:
            raise GraphQLError(f'Failed to update workflow definition: {e}')

        return MutationResult.success()

    @strawberry.mutation(description="Delete a workflow definition by slug (staff only).")
    def delete_workflow_definition(
        self, info: Info,
        slug: str,
    ) -> MutationResult:
        user = info.context.user
        _require_staff(user)

        workflow = WorkflowDefinition.objects.filter(slug=slug).first()
        if not workflow:
            raise GraphQLError(f'Workflow definition "{slug}" not found')

        if workflow.instances.exists():
            raise GraphQLError(
                f'Cannot delete workflow "{slug}" — it has {workflow.instances.count()} existing instance(s). '
                f'Disable it instead.'
            )

        try:
            workflow.delete()
        except Exception as e:
            raise GraphQLError(f'Failed to delete workflow definition: {e}')

        return MutationResult.success()

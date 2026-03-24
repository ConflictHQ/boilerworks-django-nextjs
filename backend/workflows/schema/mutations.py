from __future__ import annotations

from typing import Optional

import strawberry
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from strawberry.types import Info

from core.schema.common import MutationResult
from workflows.models import WorkflowDefinition, WorkflowInstance


@strawberry.type
class StartWorkflowResult(MutationResult):
    instance_id: Optional[strawberry.ID] = None


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

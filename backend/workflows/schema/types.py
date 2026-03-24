from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from workflows.models import TransitionLog, WorkflowDefinition, WorkflowInstance


@strawberry_django.type(WorkflowDefinition)
class WorkflowDefinitionType:
    name: str
    slug: str
    description: str
    model_label: str
    states: strawberry.scalars.JSON
    transitions: strawberry.scalars.JSON
    is_enabled: bool
    created_at: datetime

    @strawberry_django.field
    def instance_count(self) -> int:
        return self.instances.count()

    @strawberry_django.field
    def active_instance_count(self) -> int:
        return self.instances.filter(completed_at__isnull=True).count()


@strawberry.type
class AvailableTransition:
    from_state: str
    to_state: str
    label: str
    conditions_met: bool


@strawberry.type
class TransitionLogEntry:
    from_state: str
    to_state: str
    note: str
    timestamp: datetime
    username: Optional[str]


@strawberry_django.type(WorkflowInstance)
class WorkflowInstanceType:
    current_state: str
    started_at: datetime
    completed_at: Optional[datetime]
    object_id: int

    @strawberry_django.field
    def workflow_name(self) -> str:
        return self.workflow.name

    @strawberry_django.field
    def workflow_slug(self) -> str:
        return self.workflow.slug

    @strawberry_django.field
    def is_completed(self) -> bool:
        return self.completed_at is not None

    @strawberry_django.field
    def state_label(self) -> str:
        return self.workflow.get_state_label(self.current_state)

    @strawberry_django.field
    def available_transitions(self, info: Info) -> list[AvailableTransition]:
        user = info.context.user
        transitions = self.get_available_transitions(user)
        return [
            AvailableTransition(
                from_state=t['from_state'],
                to_state=t['to_state'],
                label=t.get('label', ''),
                conditions_met=t.get('conditions_met', True),
            )
            for t in transitions
        ]

    @strawberry_django.field
    def history(self) -> list[TransitionLogEntry]:
        return [
            TransitionLogEntry(
                from_state=log.from_state,
                to_state=log.to_state,
                note=log.note,
                timestamp=log.timestamp,
                username=log.transitioned_by.username if log.transitioned_by else None,
            )
            for log in self.transition_logs.select_related('transitioned_by').all()[:50]
        ]

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.types import Info

from workflows.models import WorkflowDefinition, WorkflowInstance
from workflows.schema.types import WorkflowDefinitionType, WorkflowInstanceType


@strawberry.type
class Query:

    @strawberry.field(description="List all workflow definitions.")
    def workflow_definitions(self, info: Info, model_label: Optional[str] = None) -> list[WorkflowDefinitionType]:
        qs = WorkflowDefinition.objects.filter(is_enabled=True)
        if model_label:
            qs = qs.filter(model_label=model_label)
        return qs

    @strawberry.field(description="Get a workflow definition by slug.")
    def workflow_definition(self, info: Info, slug: str) -> Optional[WorkflowDefinitionType]:
        return WorkflowDefinition.objects.filter(slug=slug).first()

    @strawberry.field(description="Get a workflow instance by ID.")
    def workflow_instance(self, info: Info, id: strawberry.ID) -> Optional[WorkflowInstanceType]:
        return WorkflowInstance.objects.filter(pk=id).first()

    @strawberry.field(description="List workflow instances for a specific object.")
    def workflow_instances(
        self, info: Info, object_id: int, model_label: Optional[str] = None,
    ) -> list[WorkflowInstanceType]:
        qs = WorkflowInstance.objects.filter(object_id=object_id)
        if model_label:
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.filter(
                app_label=model_label.split('.')[0],
                model=model_label.split('.')[-1].lower(),
            ).first()
            if ct:
                qs = qs.filter(content_type=ct)
        return qs

from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.types import Info

from forms.models import FormDefinition, FormSubmission, FormStatus
from forms.schema.types import FormDefinitionType, FormSubmissionType


@strawberry.type
class Query:

    @strawberry.field(description="Get the currently published version of a form by slug.")
    def form_definition(self, info: Info, slug: str) -> Optional[FormDefinitionType]:
        return FormDefinition.objects.get_published(slug)

    @strawberry.field(description="List all form definitions, optionally filtered by status.")
    def form_definitions(self, info: Info, status: Optional[str] = None) -> list[FormDefinitionType]:
        qs = FormDefinition.objects.all()
        if status:
            qs = qs.filter(status=status)
        return qs

    @strawberry.field(description="List submissions for a form slug, optionally filtered by status.")
    def form_submissions(
        self, info: Info, slug: str, status: Optional[str] = None,
    ) -> list[FormSubmissionType]:
        qs = FormSubmission.objects.filter(form__slug=slug)
        if status:
            qs = qs.filter(status=status)
        return qs

    @strawberry.field(description="Available field types for form schema building.")
    def form_field_types(self) -> list[str]:
        from forms.field_types import FIELD_TYPES
        return list(FIELD_TYPES.keys())

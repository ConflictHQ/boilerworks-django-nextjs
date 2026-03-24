from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from forms.models import FormDefinition, FormSubmission


@strawberry.type
class FormAnalyticsType:
    """Aggregated analytics for a form identified by slug."""
    total_submissions: int
    submissions_today: int
    avg_submissions_per_day: float
    completion_rate: float
    status_breakdown: strawberry.scalars.JSON


@strawberry_django.type(FormDefinition)
class FormDefinitionType:
    """A versioned form definition with JSON Schema."""
    name: str
    slug: str
    description: str
    status: str
    version: int
    schema: strawberry.scalars.JSON
    form_type: str
    is_public: bool
    field_config: strawberry.scalars.JSON
    logic_rules: strawberry.scalars.JSON
    scoring: strawberry.scalars.JSON
    prefill: strawberry.scalars.JSON
    published_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @strawberry_django.field
    def submission_count(self) -> int:
        return self.submissions.count()


@strawberry_django.type(FormSubmission)
class FormSubmissionType:
    """A submission against a specific form version."""
    payload: strawberry.scalars.JSON
    status: str
    submitted_at: datetime
    created_at: datetime

    @strawberry_django.field
    def form_name(self) -> str:
        return self.form.name

    @strawberry_django.field
    def form_version(self) -> int:
        return self.form.version

    @strawberry_django.field
    def form_slug(self) -> str:
        return self.form.slug

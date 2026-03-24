from __future__ import annotations

from typing import Optional

import strawberry
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.utils import timezone
from strawberry.types import Info

from forms.models import FormDefinition, FormSubmission, FormStatus, SubmissionStatus
from forms.schema.types import FormAnalyticsType, FormDefinitionType, FormSubmissionType


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

    @strawberry.field(description="Aggregated analytics for a form by slug.")
    def form_analytics(self, info: Info, slug: str) -> Optional[FormAnalyticsType]:
        qs = FormSubmission.objects.filter(form__slug=slug)
        total = qs.count()
        if total == 0:
            return FormAnalyticsType(
                total_submissions=0,
                submissions_today=0,
                avg_submissions_per_day=0.0,
                completion_rate=0.0,
                status_breakdown={},
            )

        today = timezone.now().date()
        submissions_today = qs.filter(submitted_at__date=today).count()

        # Average submissions per day: total / number of distinct days with submissions
        days_with_submissions = (
            qs.annotate(day=TruncDate('submitted_at'))
            .values('day')
            .distinct()
            .count()
        )
        avg_per_day = round(total / max(days_with_submissions, 1), 2)

        # Completion rate: submitted (non-draft) / total including drafts
        submitted_count = qs.exclude(status=SubmissionStatus.DRAFT).count()
        completion_rate = round(submitted_count / total, 4)

        # Status breakdown: count per status
        status_breakdown = dict(
            qs.values_list('status').annotate(count=Count('id')).order_by('status')
        )

        return FormAnalyticsType(
            total_submissions=total,
            submissions_today=submissions_today,
            avg_submissions_per_day=avg_per_day,
            completion_rate=completion_rate,
            status_breakdown=status_breakdown,
        )

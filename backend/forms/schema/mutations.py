from __future__ import annotations

from typing import Optional

import strawberry
from django.core.exceptions import ValidationError
from graphql import GraphQLError
from strawberry.types import Info

from core.schema.common import GlobalIDUtils, MutationResult
from forms.field_types import validate_form_schema
from forms.models import FormDefinition, FormStatus, FormSubmission


@strawberry.input
class FormDefinitionInput:
    name: str
    slug: str
    description: str = ''
    schema: strawberry.scalars.JSON = strawberry.field(default_factory=dict)


@strawberry.type
class FormSubmitResult(MutationResult):
    submission_id: Optional[strawberry.ID] = None


@strawberry.type
class Mutation:

    @strawberry.mutation(description="Create a new form definition (draft).")
    def create_form_definition(self, info: Info, input: FormDefinitionInput) -> MutationResult:
        user = info.context.user

        # Validate the schema structure
        if input.schema:
            is_valid, errors = validate_form_schema(input.schema)
            if not is_valid:
                from core.schema.common import ValidationError as VE
                return MutationResult(
                    ok=False,
                    errors=[VE(field='schema', messages=[e['message'] for e in errors])],
                )

        # Check if slug already has a draft
        existing_draft = FormDefinition.objects.filter(
            slug=input.slug, status=FormStatus.DRAFT,
        ).first()
        if existing_draft:
            return MutationResult(
                ok=False,
                errors=[MutationResult.__annotations__  # type hack — build error properly
                        and type('VE', (), {'field': 'slug', 'messages': ['A draft already exists for this slug']})()],
            )

        latest = FormDefinition.objects.get_latest(input.slug)
        version = (latest.version + 1) if latest else 1

        FormDefinition.objects.create(
            name=input.name,
            slug=input.slug,
            description=input.description,
            schema=input.schema,
            version=version,
            status=FormStatus.DRAFT,
            created_by=user,
            updated_by=user,
        )
        return MutationResult.success()

    @strawberry.mutation(description="Publish a draft form definition.")
    def publish_form(self, info: Info, slug: str) -> MutationResult:
        user = info.context.user
        form = FormDefinition.objects.filter(slug=slug, status=FormStatus.DRAFT).first()
        if not form:
            raise GraphQLError(f'No draft form found with slug "{slug}"')

        try:
            form.publish(user)
        except ValidationError as e:
            raise GraphQLError(str(e))

        return MutationResult.success()

    @strawberry.mutation(description="Archive a published form definition.")
    def archive_form(self, info: Info, slug: str) -> MutationResult:
        form = FormDefinition.objects.filter(slug=slug, status=FormStatus.PUBLISHED).first()
        if not form:
            raise GraphQLError(f'No published form found with slug "{slug}"')

        try:
            form.archive()
        except ValidationError as e:
            raise GraphQLError(str(e))

        return MutationResult.success()

    @strawberry.mutation(description="Create a new draft from an existing form's schema.")
    def new_form_draft(self, info: Info, slug: str) -> MutationResult:
        user = info.context.user
        existing = FormDefinition.objects.get_latest(slug)
        if not existing:
            raise GraphQLError(f'No form found with slug "{slug}"')

        # Check no draft already exists
        if FormDefinition.objects.filter(slug=slug, status=FormStatus.DRAFT).exists():
            raise GraphQLError(f'A draft already exists for slug "{slug}"')

        existing.new_draft(user)
        return MutationResult.success()

    @strawberry.mutation(description="Submit data against a published form. Validates payload against the form's JSON Schema.")
    def submit_form(self, info: Info, slug: str, payload: strawberry.scalars.JSON) -> FormSubmitResult:
        user = info.context.user
        form = FormDefinition.objects.get_published(slug)
        if not form:
            raise GraphQLError(f'No published form found with slug "{slug}"')

        try:
            submission = FormSubmission.submit(form, payload, user)
            return FormSubmitResult(ok=True, errors=[], submission_id=str(submission.pk))
        except ValidationError as e:
            from core.schema.common import ValidationError as VE
            if hasattr(e, 'message_dict'):
                errors = [VE(field=k, messages=v) for k, v in e.message_dict.items()]
            else:
                errors = [VE(field='payload', messages=[str(m) for m in e.messages])]
            return FormSubmitResult(ok=False, errors=errors)

    @strawberry.mutation(description="Update the status of a form submission (in_review, approved, rejected).")
    def update_submission_status(
        self, info: Info, submission_id: strawberry.ID, status: str,
    ) -> MutationResult:
        submission = FormSubmission.objects.filter(pk=submission_id).first()
        if not submission:
            raise GraphQLError(f'Submission {submission_id} not found')

        from forms.models import SubmissionStatus
        valid_statuses = [s.value for s in SubmissionStatus]
        if status not in valid_statuses:
            raise GraphQLError(f'Invalid status "{status}". Must be one of: {valid_statuses}')

        submission.status = status
        submission.updated_by = info.context.user
        submission.save()

        # Trigger notification for status change
        from forms.tasks import send_form_status_change_notification
        send_form_status_change_notification.delay(submission.pk, status)

        return MutationResult.success()

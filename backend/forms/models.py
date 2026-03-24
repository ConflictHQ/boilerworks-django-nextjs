"""Form Engine models.

FormDefinition: versioned form schemas (draft → published → archived).
FormSubmission: validated payloads pinned to a specific form version.
"""
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import BaseCoreModel, Tracking

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    jsonschema = None
    HAS_JSONSCHEMA = False


class FormType(models.TextChoices):
    STANDARD = 'standard', 'Standard'
    MULTI_STEP = 'multi_step', 'Multi-Step Wizard'
    MODAL = 'modal', 'Modal / Dialog'
    SURVEY = 'survey', 'Survey'
    ASSESSMENT = 'assessment', 'Quiz / Assessment'
    DATA_ENTRY = 'data_entry', 'Data Entry'
    PARTIAL = 'partial', 'Partial / Embeddable Fragment'


class FormStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'


class SubmissionStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft (partial save)'
    SUBMITTED = 'submitted', 'Submitted'
    IN_REVIEW = 'in_review', 'In Review'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class FormDefinitionManager(models.Manager):

    def get_published(self, slug):
        """Get the currently published version of a form by slug."""
        return self.filter(slug=slug, status=FormStatus.PUBLISHED).first()

    def get_latest(self, slug):
        """Get the highest version of a form by slug (any status)."""
        return self.filter(slug=slug).order_by('-version').first()


class FormDefinition(BaseCoreModel):
    """A versioned form definition with a JSON Schema.

    Versioning rules:
    - DRAFT: editable, not accepting submissions
    - PUBLISHED: locked, accepting submissions, only one published per slug
    - ARCHIVED: locked, no longer accepting submissions, history preserved
    - Publishing increments version and archives the previous published version
    """
    objects = FormDefinitionManager()

    # Override slug from BaseCoreModel to remove unique=True
    # (multiple versions share the same slug, uniqueness is on slug+version)
    slug = models.SlugField(max_length=250, db_index=True, default='')

    form_type = models.CharField(
        max_length=20,
        choices=FormType.choices,
        default=FormType.STANDARD,
        help_text='Controls rendering behavior (multi-step, modal, survey, etc.)',
    )
    status = models.CharField(
        max_length=20,
        choices=FormStatus.choices,
        default=FormStatus.DRAFT,
        db_index=True,
    )
    schema = models.JSONField(
        default=dict,
        help_text='JSON Schema defining the form fields, types, and validation rules',
    )
    field_config = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Per-field configuration beyond JSON Schema. Keys are field names, values are objects with: '
            'weight (numeric, for scoring), question_type (rating/scale/matrix/ranking/etc.), '
            'step (int, for multi-step forms), order (int, display sequence), '
            'randomize (bool, shuffle options for surveys), '
            'logic (conditional visibility rules), '
            'placeholder, help_text, x-widget override.'
        ),
    )
    logic_rules = models.JSONField(
        default=list,
        blank=True,
        help_text=(
            'Form-level logic rules. Each rule: '
            '{"condition": {"field": "X", "op": "eq|neq|gt|lt|in|contains", "value": ...}, '
            '"action": "show|hide|skip_to|require|set_value", "target": "field_or_step_name"}'
        ),
    )
    scoring = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Scoring configuration for assessments/quizzes. '
            '{"total_points": N, "passing_score": N, "show_results": bool}'
        ),
    )
    prefill = models.JSONField(
        default=dict,
        blank=True,
        help_text=(
            'Prefill configuration. Maps field names to data sources: '
            '{"field_name": {"source": "user_profile|url_param|previous_submission|static", "key": "..."}}'
        ),
    )
    version = models.PositiveIntegerField(default=1)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='published_forms',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['slug', 'version'],
                name='unique_form_slug_version',
            ),
        ]
        ordering = ['-version']

    def publish(self, user):
        """Publish this form definition.

        Archives any existing published version of the same slug,
        sets this version as published, and locks it.
        """
        if self.status != FormStatus.DRAFT:
            raise ValidationError('Only draft forms can be published.')

        # Archive any currently published version
        FormDefinition.objects.filter(
            slug=self.slug, status=FormStatus.PUBLISHED,
        ).update(status=FormStatus.ARCHIVED)

        self.status = FormStatus.PUBLISHED
        self.published_at = timezone.now()
        self.published_by = user
        self.save()

    def archive(self):
        """Archive this form definition."""
        if self.status != FormStatus.PUBLISHED:
            raise ValidationError('Only published forms can be archived.')
        self.status = FormStatus.ARCHIVED
        self.save()

    def new_draft(self, user):
        """Create a new draft version based on this form's schema."""
        latest = FormDefinition.objects.get_latest(self.slug)
        new_version = (latest.version if latest else 0) + 1
        return FormDefinition.objects.create(
            name=self.name,
            slug=self.slug,
            description=self.description,
            schema=self.schema,
            version=new_version,
            status=FormStatus.DRAFT,
            created_by=user,
            updated_by=user,
        )

    def validate_payload(self, payload):
        """Validate a submission payload against this form's JSON Schema.

        Returns (is_valid, errors) tuple.
        """
        if not self.schema:
            return True, []

        if not HAS_JSONSCHEMA:
            return True, []

        validator = jsonschema.Draft7Validator(self.schema)
        errors = list(validator.iter_errors(payload))
        if errors:
            return False, [
                {'path': '.'.join(str(p) for p in e.absolute_path), 'message': e.message}
                for e in errors
            ]
        return True, []

    def __str__(self):
        return f'{self.name} v{self.version} ({self.status})'


class FormSubmission(Tracking):
    """A submission against a specific FormDefinition version.

    The form FK is immutable — once submitted, the schema version is locked.
    """
    form = models.ForeignKey(
        FormDefinition,
        on_delete=models.PROTECT,
        related_name='submissions',
        help_text='The exact form version this submission was created against',
    )
    payload = models.JSONField(
        default=dict,
        help_text='Submitted data, validated against the form schema at submit time',
    )
    secure_payload = models.BinaryField(
        null=True, blank=True,
        help_text='Encrypted fields (fields marked secure in field_config are stored here, not in payload)',
    )
    status = models.CharField(
        max_length=20,
        choices=SubmissionStatus.choices,
        default=SubmissionStatus.SUBMITTED,
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='form_submissions',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    signed_by = models.ForeignKey(
        'core.PinTransaction',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='form_submissions',
        help_text='PIN transaction used to sign this submission (if form requires signature)',
    )
    organization = models.ForeignKey(
        'organization.Organization',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='form_submissions',
    )

    class Meta:
        ordering = ['-submitted_at']

    @classmethod
    def submit(cls, form, payload, user):
        """Validate and create a submission.

        Raises ValidationError if the form is not published or payload is invalid.
        """
        if form.status != FormStatus.PUBLISHED:
            raise ValidationError('Can only submit to published forms.')

        is_valid, errors = form.validate_payload(payload)
        if not is_valid:
            raise ValidationError(errors)

        org = None
        try:
            org = user.profile.organization()
        except Exception:
            pass

        return cls.objects.create(
            form=form,
            payload=payload,
            submitted_by=user,
            organization=org,
            created_by=user,
            updated_by=user,
        )

    def __str__(self):
        return f'Submission #{self.pk} for {self.form}'

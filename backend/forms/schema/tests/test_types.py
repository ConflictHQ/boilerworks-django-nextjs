"""Form Engine tests — model lifecycle, versioning, validation, GraphQL integration."""
from django.contrib.auth import get_user_model
from django.contrib.sessions.backends.db import SessionStore
from django.core.exceptions import ValidationError
from django.test import TestCase

from config.schema import schema
from core.schema.context import StrawberryContext
from forms.field_types import FIELD_TYPES, evaluate_calculation, validate_form_schema
from forms.models import (
    FormDefinition,
    FormStatus,
    FormSubmission,
    FormType,
    SubmissionStatus,
)

User = get_user_model()


class FakeRequest:
    def __init__(self, user):
        self.user = user
        self.session = SessionStore()
        self.session.create()
        self.headers = {}


class FormDefinitionModelTest(TestCase):

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='FormOrg')
        self.user = User.objects.create_superuser(
            username='form_user', email='form@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def test_create_draft(self):
        form = FormDefinition.objects.create(
            name='Expense Report', slug='expense-report',
            schema={'type': 'object', 'properties': {'amount': {'type': 'number'}}},
            created_by=self.user, updated_by=self.user,
        )
        self.assertEqual(form.status, FormStatus.DRAFT)
        self.assertIsNotNone(form.pk)

    def test_publish_sets_status_and_timestamp(self):
        form = FormDefinition.objects.create(
            name='Contact', slug='contact-form',
            schema={'type': 'object', 'properties': {'name': {'type': 'string'}}},
            created_by=self.user, updated_by=self.user,
        )
        form.publish(self.user)
        form.refresh_from_db()
        self.assertEqual(form.status, FormStatus.PUBLISHED)
        self.assertIsNotNone(form.published_at)

    def test_publish_archives_previous(self):
        v1 = FormDefinition.objects.create(
            name='Feedback', slug='feedback', version=100, status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'rating': {'type': 'integer'}}},
            created_by=self.user, updated_by=self.user,
        )
        v2 = FormDefinition.objects.create(
            name='Feedback', slug='feedback', version=200, status=FormStatus.DRAFT,
            schema={'type': 'object', 'properties': {'rating': {'type': 'integer'}}},
            created_by=self.user, updated_by=self.user,
        )
        v2.publish(self.user)
        v1.refresh_from_db()
        self.assertEqual(v1.status, FormStatus.ARCHIVED)

    def test_cannot_publish_non_draft(self):
        form = FormDefinition.objects.create(
            name='Locked', slug='locked', status=FormStatus.PUBLISHED,
            created_by=self.user, updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            form.publish(self.user)

    def test_new_draft_creates_higher_version(self):
        form = FormDefinition.objects.create(
            name='Versioned', slug='versioned', version=100, status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'x': {'type': 'string'}}},
            created_by=self.user, updated_by=self.user,
        )
        draft = form.new_draft(self.user)
        self.assertGreater(draft.version, form.version)
        self.assertEqual(draft.status, FormStatus.DRAFT)

    def test_form_type_default(self):
        form = FormDefinition.objects.create(
            name='Default', slug='default-type', created_by=self.user, updated_by=self.user,
        )
        self.assertEqual(form.form_type, FormType.STANDARD)


class FormSubmissionTest(TestCase):

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='SubOrg')
        self.user = User.objects.create_superuser(
            username='sub_user', email='sub@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()
        self.form = FormDefinition.objects.create(
            name='Test Form', slug='test-form', status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'name': {'type': 'string'}, 'amount': {'type': 'number'}}, 'required': ['name']},
            created_by=self.user, updated_by=self.user,
        )

    def test_submit_valid(self):
        sub = FormSubmission.submit(self.form, {'name': 'Test', 'amount': 42.5}, self.user)
        self.assertEqual(sub.status, SubmissionStatus.SUBMITTED)
        self.assertEqual(sub.payload['name'], 'Test')

    def test_submit_invalid_raises(self):
        with self.assertRaises(ValidationError):
            FormSubmission.submit(self.form, {'amount': 'not a number'}, self.user)

    def test_submit_missing_required_raises(self):
        with self.assertRaises(ValidationError):
            FormSubmission.submit(self.form, {'amount': 10}, self.user)

    def test_cannot_submit_to_draft(self):
        draft = FormDefinition.objects.create(
            name='Draft', slug='draft-only', status=FormStatus.DRAFT,
            created_by=self.user, updated_by=self.user,
        )
        with self.assertRaises(ValidationError):
            FormSubmission.submit(draft, {'name': 'test'}, self.user)


class SchemaValidationTest(TestCase):

    def test_valid_schema(self):
        is_valid, _ = validate_form_schema({'type': 'object', 'properties': {'x': {'type': 'string'}}, 'required': ['x']})
        self.assertTrue(is_valid)

    def test_missing_root_type(self):
        is_valid, _ = validate_form_schema({'properties': {'x': {'type': 'string'}}})
        self.assertFalse(is_valid)

    def test_empty_properties(self):
        is_valid, _ = validate_form_schema({'type': 'object', 'properties': {}})
        self.assertFalse(is_valid)

    def test_required_not_in_properties(self):
        is_valid, _ = validate_form_schema({'type': 'object', 'properties': {'x': {'type': 'string'}}, 'required': ['missing']})
        self.assertFalse(is_valid)


class CalculationTest(TestCase):

    def test_sum(self):
        self.assertEqual(evaluate_calculation({'op': 'sum', 'fields': ['a', 'b']}, {'a': 10, 'b': 20}), 30)

    def test_avg(self):
        self.assertEqual(evaluate_calculation({'op': 'avg', 'fields': ['a', 'b']}, {'a': 10, 'b': 30}), 20)

    def test_percentage(self):
        self.assertEqual(evaluate_calculation({'op': 'percentage', 'fields': ['p', 't']}, {'p': 25, 't': 100}), 25.0)

    def test_display_from(self):
        self.assertEqual(evaluate_calculation({'op': 'display_from', 'field': 'name'}, {'name': 'Acme'}), 'Acme')

    def test_expression(self):
        self.assertEqual(evaluate_calculation({'op': 'expression', 'expr': 'qty * price'}, {'qty': 5, 'price': 10}), 50)

    def test_missing_fields(self):
        self.assertIsNone(evaluate_calculation({'op': 'sum', 'fields': ['x']}, {}))


class FieldTypesTest(TestCase):

    def test_registry_not_empty(self):
        self.assertGreater(len(FIELD_TYPES), 15)

    def test_all_have_type_and_description(self):
        for name, cfg in FIELD_TYPES.items():
            self.assertIn('type', cfg, f'{name} missing type')
            self.assertIn('description', cfg, f'{name} missing description')


class GraphQLFormTest(TestCase):

    def setUp(self):
        from organization.models import Organization, OrganizationMember
        self.org = Organization.objects.create(name='GQLOrg')
        self.user = User.objects.create_superuser(
            username='gql_form', email='gqlf@test.com', password='testpass',
        )
        OrganizationMember.objects.create(
            organization=self.org, member=self.user, is_active=True,
        )
        self.user.profile.active_organization = self.org
        self.user.profile.save()

    def _ctx(self):
        return StrawberryContext(FakeRequest(self.user))

    def test_field_types_query(self):
        result = schema.execute_sync('{ formFieldTypes }', context_value=self._ctx())
        self.assertIsNone(result.errors)
        self.assertIn('text', result.data['formFieldTypes'])
        self.assertIn('repeatable', result.data['formFieldTypes'])

    def test_query_published_form(self):
        FormDefinition.objects.create(
            name='Query Test', slug='query-test', status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'x': {'type': 'string'}}},
            created_by=self.user, updated_by=self.user,
        )
        result = schema.execute_sync(
            '{ formDefinition(slug: "query-test") { name status version } }',
            context_value=self._ctx(),
        )
        self.assertIsNone(result.errors)
        self.assertEqual(result.data['formDefinition']['name'], 'Query Test')

    def test_submit_mutation(self):
        FormDefinition.objects.create(
            name='Submit', slug='submit-test', status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'msg': {'type': 'string'}}, 'required': ['msg']},
            created_by=self.user, updated_by=self.user,
        )
        result = schema.execute_sync(
            'mutation { submitForm(slug: "submit-test", payload: {msg: "hi"}) { ok submissionId } }',
            context_value=self._ctx(),
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['submitForm']['ok'])

    def test_publish_mutation(self):
        FormDefinition.objects.create(
            name='Pub', slug='pub-test', status=FormStatus.DRAFT,
            created_by=self.user, updated_by=self.user,
        )
        result = schema.execute_sync(
            'mutation { publishForm(slug: "pub-test") { ok } }',
            context_value=self._ctx(),
        )
        self.assertIsNone(result.errors)
        self.assertTrue(result.data['publishForm']['ok'])

    def test_submit_validation_error(self):
        FormDefinition.objects.create(
            name='Val', slug='val-test', status=FormStatus.PUBLISHED,
            schema={'type': 'object', 'properties': {'count': {'type': 'integer'}}, 'required': ['count']},
            created_by=self.user, updated_by=self.user,
        )
        result = schema.execute_sync(
            'mutation { submitForm(slug: "val-test", payload: {count: "bad"}) { ok errors { field } } }',
            context_value=self._ctx(),
        )
        self.assertIsNone(result.errors)
        self.assertFalse(result.data['submitForm']['ok'])

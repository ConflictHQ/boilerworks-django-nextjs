"""
Scaffold a new Boilerworks app with all conventions wired.

Usage:
    python manage.py scaffold app --name=crm
    python manage.py scaffold app --name=crm --model=Lead --fields=name:str,value:decimal,source:str
"""
import os
import textwrap

from django.core.management.base import BaseCommand


FIELD_TYPE_MAP = {
    'str': 'models.CharField(max_length=255, blank=True)',
    'text': 'models.TextField(blank=True)',
    'int': 'models.IntegerField(default=0)',
    'decimal': 'models.DecimalField(max_digits=10, decimal_places=2, default=0)',
    'bool': 'models.BooleanField(default=False)',
    'date': 'models.DateField(null=True, blank=True)',
    'datetime': 'models.DateTimeField(null=True, blank=True)',
    'json': 'models.JSONField(default=dict, blank=True)',
    'fk': 'models.ForeignKey("{target}", null=True, blank=True, on_delete=models.SET_NULL)',
}

STRAWBERRY_TYPE_MAP = {
    'str': 'Optional[str]',
    'text': 'Optional[str]',
    'int': 'int',
    'decimal': 'Optional[str]',
    'bool': 'bool',
    'date': 'Optional[datetime]',
    'datetime': 'Optional[datetime]',
    'json': 'Optional[strawberry.scalars.JSON]',
    'fk': 'Optional[strawberry.ID]',
}


class Command(BaseCommand):
    help = "Scaffold a new Boilerworks app with models, admin, schema, serializers, and tests"

    def add_arguments(self, parser):
        parser.add_argument('type', choices=['app', 'form', 'workflow'], help='What to scaffold')
        parser.add_argument('--name', required=True, help='App/form/workflow name')
        parser.add_argument('--model', default='', help='Primary model name (PascalCase, for app type)')
        parser.add_argument('--fields', default='', help='Fields as name:type pairs (e.g. name:str,value:decimal)')
        parser.add_argument('--slug', default='', help='Form slug (for form type)')
        parser.add_argument('--states', default='', help='Comma-separated workflow states (for workflow type)')

    def handle(self, *args, **options):
        scaffold_type = options['type']

        if scaffold_type == 'form':
            return self._scaffold_form(options)
        if scaffold_type == 'workflow':
            return self._scaffold_workflow(options)

        app_name = options['name']
        model_name = options['model'] or app_name.replace('_', ' ').title().replace(' ', '')
        fields_str = options['fields']

        fields = []
        if fields_str:
            for pair in fields_str.split(','):
                name, ftype = pair.strip().split(':')
                fields.append((name.strip(), ftype.strip()))

        base_dir = os.path.join(os.getcwd(), app_name)
        if os.path.exists(base_dir):
            self.stderr.write(self.style.ERROR(f'Directory {app_name}/ already exists'))
            return

        self.stdout.write(f'Scaffolding app: {app_name} with model: {model_name}')

        dirs = [
            base_dir,
            os.path.join(base_dir, 'migrations'),
            os.path.join(base_dir, 'schema'),
            os.path.join(base_dir, 'schema', 'tests'),
            os.path.join(base_dir, 'serializers'),
            os.path.join(base_dir, 'tests'),
        ]
        for d in dirs:
            os.makedirs(d, exist_ok=True)

        files = {
            '__init__.py': '',
            'apps.py': self._apps(app_name),
            'models.py': self._models(app_name, model_name, fields),
            'admin.py': self._admin(model_name),
            'views.py': '',
            'migrations/__init__.py': '',
            'serializers/__init__.py': self._serializer(app_name, model_name, fields),
            'schema/__init__.py': self._schema_init(),
            'schema/types.py': self._schema_types(app_name, model_name, fields),
            'schema/queries.py': self._schema_queries(app_name, model_name),
            'schema/mutations.py': self._schema_mutations(app_name, model_name),
            'schema/tests/__init__.py': '',
            'schema/tests/test_types.py': self._schema_tests(app_name, model_name),
            'tests/__init__.py': '',
        }

        for path, content in files.items():
            full_path = os.path.join(base_dir, path)
            with open(full_path, 'w') as f:
                f.write(content)

        self.stdout.write(self.style.SUCCESS(f'\nScaffolded {app_name}/'))
        self.stdout.write(f'  Model:      {model_name}')
        self.stdout.write(f'  Fields:     {len(fields)}')
        self.stdout.write(f'  Files:      {len(files)}')
        self.stdout.write('')
        self.stdout.write('Next steps:')
        self.stdout.write(f"  1. Add '{app_name}' to INSTALLED_APPS in config/settings.py")
        self.stdout.write(f'  2. Wire schema into config/schema.py:')
        self.stdout.write(f'     import {app_name}.schema as {model_name}Schema')
        self.stdout.write(f'  3. Run: make migrations && make migrate')
        self.stdout.write(f'  4. Run: make test')

    def _apps(self, app_name):
        return textwrap.dedent(f"""\
            from django.apps import AppConfig


            class {app_name.replace('_', ' ').title().replace(' ', '')}Config(AppConfig):
                default_auto_field = 'django.db.models.BigAutoField'
                name = '{app_name}'
        """)

    def _models(self, app_name, model_name, fields):
        lines = [
            'from core.models import BaseCoreModel',
            'from django.db import models',
            '',
            '',
            f'class {model_name}(BaseCoreModel):',
            f'    """TODO: Add model description."""',
        ]
        if fields:
            for name, ftype in fields:
                django_field = FIELD_TYPE_MAP.get(ftype, f'models.CharField(max_length=255)  # unknown type: {ftype}')
                lines.append(f'    {name} = {django_field}')
        else:
            lines.append('    pass')
        lines.append('')
        return '\n'.join(lines)

    def _admin(self, model_name):
        return textwrap.dedent(f"""\
            from core.utils.admin import BaseCoreAdmin
            from django.contrib import admin

            from .models import {model_name}


            @admin.register({model_name})
            class {model_name}Admin(BaseCoreAdmin):
                list_display = ('name', 'slug', 'created_at')
                search_fields = ('name', 'slug')
        """)

    def _serializer(self, app_name, model_name, fields):
        field_names = ', '.join([f"'{name}'" for name, _ in fields]) if fields else "'name', 'description'"
        return textwrap.dedent(f"""\
            from rest_framework import serializers

            from {app_name}.models import {model_name}


            class {model_name}Serializer(serializers.ModelSerializer):
                class Meta:
                    model = {model_name}
                    fields = ({field_names},)
        """)

    def _schema_init(self):
        return textwrap.dedent("""\
            from .mutations import Mutation
            from .queries import Query

            __all__ = ['Query', 'Mutation']
        """)

    def _schema_types(self, app_name, model_name, fields):
        lines = [
            'from __future__ import annotations',
            '',
            'from datetime import datetime',
            'from typing import Optional',
            '',
            'import strawberry',
            'import strawberry_django',
            'from strawberry.types import Info',
            '',
            'from core.schema.common import permission_filtered_queryset',
            f'from {app_name}.models import {model_name}',
            '',
            '',
            f'@strawberry_django.type({model_name})',
            f'class {model_name}Type:',
            f'    """GraphQL type for {model_name}."""',
        ]
        if fields:
            for name, ftype in fields:
                strawberry_type = STRAWBERRY_TYPE_MAP.get(ftype, 'Optional[str]')
                lines.append(f'    {name}: {strawberry_type}')
        lines.append('')
        lines.append('    @classmethod')
        lines.append('    def get_queryset(cls, queryset, info: Info):')
        lines.append('        return permission_filtered_queryset(queryset, info)')
        lines.append('')
        return '\n'.join(lines)

    def _schema_queries(self, app_name, model_name):
        lower = model_name[0].lower() + model_name[1:]
        return textwrap.dedent(f"""\
            from __future__ import annotations

            from typing import Optional

            import strawberry
            import strawberry_django
            from strawberry.types import Info

            from {app_name}.models import {model_name}
            from {app_name}.schema.types import {model_name}Type


            @strawberry.type
            class Query:

                @strawberry.field
                def {lower}s(self, info: Info, search: str = '') -> list[{model_name}Type]:
                    qs = {model_name}.objects.all()
                    if search:
                        qs = qs.filter(name__icontains=search)
                    return qs

                @strawberry.field
                def {lower}(self, info: Info, slug: str) -> Optional[{model_name}Type]:
                    return {model_name}.objects.filter(slug=slug).first()
        """)

    def _schema_mutations(self, app_name, model_name):
        lower = model_name[0].lower() + model_name[1:]
        return textwrap.dedent(f"""\
            from __future__ import annotations

            import strawberry
            from strawberry.types import Info

            from core.schema.common import MutationResult
            from core.schema.mutations.base import restricted_serializer_mutate
            from {app_name}.models import {model_name}
            from {app_name}.serializers import {model_name}Serializer


            @strawberry.type
            class Mutation:

                @strawberry.mutation
                def {lower}(self, info: Info, input: strawberry.scalars.JSON) -> MutationResult:
                    \"\"\"{model_name} upsert mutation.\"\"\"
                    instance = None
                    pk = input.pop('id', None)
                    if pk:
                        instance = {model_name}.objects.filter(pk=pk).first()
                    return restricted_serializer_mutate(
                        {model_name}Serializer, {model_name}, info,
                        data=input, instance=instance,
                    )
        """)

    def _schema_tests(self, app_name, model_name):
        return textwrap.dedent(f"""\
            from django.contrib.auth import get_user_model
            from django.test import TestCase

            from {app_name}.models import {model_name}

            User = get_user_model()


            class {model_name}TypeTest(TestCase):

                def setUp(self):
                    from organization.models import Organization, OrganizationMember
                    self.org = Organization.objects.create(name='TestOrg')
                    self.user = User.objects.create_superuser(
                        username='{lower}_test', email='{lower}@test.com', password='testpass',
                    )
                    OrganizationMember.objects.create(
                        organization=self.org, member=self.user, is_active=True,
                    )
                    self.user.profile.active_organization = self.org
                    self.user.profile.save()

                    self.instance = {model_name}.objects.create(
                        name='Test {model_name}',
                        created_by=self.user,
                        updated_by=self.user,
                    )

                def test_instance_created(self):
                    obj = {model_name}.objects.get(pk=self.instance.pk)
                    self.assertEqual(obj.name, 'Test {model_name}')
                    self.assertIsNotNone(obj.guid)
                    self.assertIsNotNone(obj.slug)

                def test_instance_has_tracking_fields(self):
                    obj = {model_name}.objects.get(pk=self.instance.pk)
                    self.assertIsNotNone(obj.created_at)
                    self.assertIsNotNone(obj.updated_at)
                    self.assertEqual(obj.created_by, self.user)
        """.format(lower=model_name[0].lower() + model_name[1:]))

    def _schema_tests(self, app_name, model_name):
        lower = model_name[0].lower() + model_name[1:]
        return textwrap.dedent(f"""\
            from django.contrib.auth import get_user_model
            from django.test import TestCase

            from {app_name}.models import {model_name}

            User = get_user_model()


            class {model_name}TypeTest(TestCase):

                def setUp(self):
                    from organization.models import Organization, OrganizationMember
                    self.org = Organization.objects.create(name='TestOrg')
                    self.user = User.objects.create_superuser(
                        username='{lower}_test', email='{lower}@test.com', password='testpass',
                    )
                    OrganizationMember.objects.create(
                        organization=self.org, member=self.user, is_active=True,
                    )
                    self.user.profile.active_organization = self.org
                    self.user.profile.save()

                    self.instance = {model_name}.objects.create(
                        name='Test {model_name}',
                        created_by=self.user,
                        updated_by=self.user,
                    )

                def test_instance_created(self):
                    obj = {model_name}.objects.get(pk=self.instance.pk)
                    self.assertEqual(obj.name, 'Test {model_name}')
                    self.assertIsNotNone(obj.guid)
                    self.assertIsNotNone(obj.slug)

                def test_instance_has_tracking_fields(self):
                    obj = {model_name}.objects.get(pk=self.instance.pk)
                    self.assertIsNotNone(obj.created_at)
                    self.assertIsNotNone(obj.updated_at)
                    self.assertEqual(obj.created_by, self.user)
        """)

    def _scaffold_form(self, options):
        """Create a FormDefinition from CLI arguments."""
        name = options['name']
        slug = options.get('slug') or name.lower().replace(' ', '-').replace('_', '-')
        fields_str = options.get('fields', '')

        properties = {}
        required = []
        if fields_str:
            for pair in fields_str.split(','):
                fname, ftype = pair.strip().split(':')
                fname = fname.strip()
                ftype = ftype.strip()
                from forms.field_types import FIELD_TYPES
                schema_fragment = FIELD_TYPES.get(ftype, {'type': 'string'})
                properties[fname] = {k: v for k, v in schema_fragment.items() if k != 'description' and k != 'x-widget'}
                properties[fname]['title'] = fname.replace('_', ' ').title()
                required.append(fname)

        schema = {
            'type': 'object',
            'properties': properties,
            'required': required,
        }

        self.stdout.write(f'Creating form definition: {name} (slug: {slug})')
        self.stdout.write(f'  Fields: {len(properties)}')
        self.stdout.write(f'  Schema:')
        import json
        self.stdout.write(json.dumps(schema, indent=2))
        self.stdout.write('')

        from forms.models import FormDefinition
        form = FormDefinition.objects.create(
            name=name,
            slug=slug,
            schema=schema,
        )
        self.stdout.write(self.style.SUCCESS(f'Created FormDefinition pk={form.pk} slug={slug} (draft)'))
        self.stdout.write(f'  Publish with: python manage.py shell -c "from forms.models import FormDefinition; FormDefinition.objects.get(slug=\'{slug}\').publish(None)"')

    def _scaffold_workflow(self, options):
        """Stub for workflow scaffolding — prints the definition structure."""
        name = options['name']
        states_str = options.get('states', '')

        if not states_str:
            self.stderr.write(self.style.ERROR('--states is required for workflow scaffolding'))
            return

        states = [s.strip() for s in states_str.split(',')]

        definition = {
            'name': name,
            'slug': name.lower().replace(' ', '-'),
            'states': [],
            'transitions': [],
        }

        for i, state in enumerate(states):
            definition['states'].append({
                'name': state,
                'label': state.replace('_', ' ').title(),
                'is_initial': i == 0,
                'is_final': i == len(states) - 1,
                'color': '#22c55e' if i == len(states) - 1 else '#6b7280',
            })

        # Auto-generate linear transitions
        for i in range(len(states) - 1):
            definition['transitions'].append({
                'from_state': states[i],
                'to_state': states[i + 1],
                'label': f'{states[i]} → {states[i + 1]}',
                'conditions': [],
                'actions': [],
            })

        import json
        self.stdout.write(f'Workflow definition for: {name}')
        self.stdout.write(json.dumps(definition, indent=2))
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Note: Workflow Engine (#2) not yet implemented.'))
        self.stdout.write('This output can be used as the WorkflowDefinition.states/transitions JSON when it ships.')

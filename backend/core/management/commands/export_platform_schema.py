"""Export the full platform schema as a machine-readable JSON manifest.

An agent reads this to understand every model, field, relationship,
permission, GraphQL type/query/mutation, form definition, and feature
toggle — without grepping source code.

Usage:
    python manage.py export_platform_schema
    python manage.py export_platform_schema --pretty
    python manage.py export_platform_schema > platform.json
"""
import json

from django.apps import apps
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export the full platform schema as JSON for AI agents"

    def add_arguments(self, parser):
        parser.add_argument('--pretty', action='store_true', help='Pretty-print JSON')

    def handle(self, *args, **options):
        manifest = {
            'platform': 'boilerworks',
            'version': self._get_version(),
            'features': self._get_features(),
            'models': self._get_models(),
            'graphql': self._get_graphql(),
            'permissions': self._get_permissions(),
            'forms': self._get_forms(),
            'apps': self._get_apps(),
        }

        indent = 2 if options['pretty'] else None
        self.stdout.write(json.dumps(manifest, indent=indent, default=str))

    def _get_version(self):
        from django.conf import settings
        return getattr(settings, 'VERSION', 'unknown')

    def _get_features(self):
        from config.features import Feature, is_enabled
        return {f.value: is_enabled(f) for f in Feature}

    def _get_models(self):
        models = []
        skip_apps = {'admin', 'auth', 'contenttypes', 'sessions', 'django_celery_beat',
                      'django_celery_results', 'django_ses', 'constance', 'health_check'}

        for model in apps.get_models():
            app_label = model._meta.app_label
            if app_label in skip_apps:
                continue

            fields = []
            for field in model._meta.get_fields():
                field_info = {'name': field.name, 'type': type(field).__name__}
                if hasattr(field, 'max_length') and field.max_length:
                    field_info['max_length'] = field.max_length
                if hasattr(field, 'null'):
                    field_info['nullable'] = field.null
                if hasattr(field, 'choices') and field.choices:
                    field_info['choices'] = [c[0] for c in field.choices]
                if hasattr(field, 'related_model') and field.related_model:
                    field_info['related_to'] = f'{field.related_model._meta.app_label}.{field.related_model.__name__}'
                if hasattr(field, 'help_text') and field.help_text:
                    field_info['help_text'] = str(field.help_text)
                fields.append(field_info)

            model_info = {
                'app': app_label,
                'name': model.__name__,
                'table': model._meta.db_table,
                'fields': fields,
            }

            # Check for custom permissions
            if hasattr(model._meta, 'permissions') and model._meta.permissions:
                model_info['custom_permissions'] = [
                    {'codename': p[0], 'name': p[1]}
                    for p in model._meta.permissions
                ]

            # Check for model-level permission system
            if hasattr(model, 'p'):
                model_info['has_field_permissions'] = True

            models.append(model_info)

        return models

    def _get_graphql(self):
        try:
            from config.schema import schema
            sdl = schema.as_str()

            # Parse types, queries, mutations from SDL
            types = []
            queries = []
            mutations = []
            subscriptions = []

            for line in sdl.split('\n'):
                line = line.strip()
                if line.startswith('type ') and '{' in line:
                    type_name = line.split('{')[0].replace('type ', '').strip()
                    if type_name not in ('Query', 'Mutation', 'Subscription'):
                        types.append(type_name)
                elif '(' in line and ':' in line and not line.startswith('#') and not line.startswith('"'):
                    field_name = line.split('(')[0].strip()
                    if field_name:
                        # Determine if it's a query, mutation, or subscription based on context
                        pass

            # Use introspection for accurate field lists
            result = schema.execute_sync('''
                {
                    __schema {
                        queryType { fields { name description args { name type { name } } type { name kind ofType { name } } } }
                        mutationType { fields { name description args { name type { name } } type { name kind ofType { name } } } }
                        subscriptionType { fields { name description } }
                    }
                }
            ''')

            if result.data:
                s = result.data['__schema']
                queries = [
                    {'name': f['name'], 'description': f.get('description', ''),
                     'args': [a['name'] for a in f.get('args', [])]}
                    for f in s['queryType']['fields']
                    if not f['name'].startswith('_')
                ]
                mutations = [
                    {'name': f['name'], 'description': f.get('description', ''),
                     'args': [a['name'] for a in f.get('args', [])]}
                    for f in s['mutationType']['fields']
                ]
                sub_type = s.get('subscriptionType')
                if sub_type:
                    subscriptions = [
                        {'name': f['name'], 'description': f.get('description', '')}
                        for f in sub_type['fields']
                    ]

            return {
                'types': types,
                'queries': queries,
                'mutations': mutations,
                'subscriptions': subscriptions,
                'sdl_length': len(sdl),
            }
        except Exception as e:
            return {'error': str(e)}

    def _get_permissions(self):
        try:
            from config.roles_gen import P
            return [
                {'name': p.name, 'value': p.value}
                for p in P
            ]
        except Exception:
            return []

    def _get_forms(self):
        try:
            from forms.models import FormDefinition
            return [
                {
                    'name': f.name,
                    'slug': f.slug,
                    'status': f.status,
                    'version': f.version,
                    'form_type': f.form_type,
                    'is_public': f.is_public,
                    'field_count': len((f.schema or {}).get('properties', {})),
                    'submission_count': f.submissions.count(),
                }
                for f in FormDefinition.objects.all()
            ]
        except Exception:
            return []

    def _get_apps(self):
        boilerworks_apps = []
        for config in apps.get_app_configs():
            if config.name.startswith('django.') or config.name in (
                'corsheaders', 'debug_toolbar', 'strawberry_django',
                'phonenumber_field', 'rolepermissions', 'django_filters',
                'djmoney', 'nested_admin', 'sslserver', 'storages',
                'django_crontab', 'import_export', 'simple_history',
                'constance', 'health_check',
            ):
                continue
            boilerworks_apps.append({
                'name': config.name,
                'label': config.label,
                'models': [m.__name__ for m in config.get_models()],
            })
        return boilerworks_apps

import importlib
import json
import logging
import os
from importlib.resources import files

from django.core.management import call_command
from django.db import migrations

LOAD_DATA_COMMAND = 'loaddata'

logger = logging.getLogger(__name__)


def remove_migration_on_unapply(app, name):
    """
    The issue is that when you unapply or replace a migration in Django, the record of that migration in the
    django_migrations table is not automatically updated or deleted, potentially causing confusion and problems
    when managing database migrations.
    """
    name = name.split('.')[-1]
    return [
        migrations.RunSQL(
            sql=f"select * from django_migrations where app = '{app}' and name = '{name}';",
            reverse_sql=f"delete from django_migrations where app = '{app}' and name = '{name}';",
        )
    ]


class LoadFixture(migrations.RunPython):

    def __init__(self, package, fixture):
        self.package = package
        self.fixture = fixture
        migrations.RunPython.__init__(self, code=self.load_data_from_file, reverse_code=self.remove_data_from_file)

    def load_data_from_file(self, apps, schema_editor):
        if os.getenv('DJANGO_CONFIGURATION') != 'Tests' or os.getenv('DJANGO_LOAD_FIXTURES') == 'False':
            return
        if not files(self.package).joinpath(self.fixture).is_file():
            return
        with importlib.resources.path(self.package, self.fixture) as resource:
            call_command(LOAD_DATA_COMMAND, "--ignorenonexistent", resource, verbosity=2)

    def remove_data_from_file(self, apps, schema_editor):
        if not files(self.package).joinpath(self.fixture).is_file():
            return
        with importlib.resources.open_text(self.package, self.fixture) as fixture:
            fixture_json = json.load(fixture)
            for instance in fixture_json[::-1]:
                application, model_name = instance['model'].split('.')
                if 'pk' not in instance:
                    continue
                pk = instance['pk']
                try:
                    model = apps.get_model(application, model_name)
                    model.objects.filter(pk=pk).delete()
                except Exception as e:
                    logger.error(f'Unable to delete object {application}:{model_name}:{pk}: {e}')

    def deconstruct(self):
        kwargs = {
            "package": self.package,
            "fixture": self.fixture,
        }
        if self.reverse_code is not None:
            kwargs["reverse_code"] = self.reverse_code
        if self.atomic is not None:
            kwargs["atomic"] = self.atomic
        if self.hints:
            kwargs["hints"] = self.hints
        return self.__class__.__qualname__, [], kwargs


class LoadPermissions(migrations.RunPython):

    def __init__(self, package, fixture):
        self.package = package
        self.fixture = fixture
        migrations.RunPython.__init__(self, code=self.load_data_from_file, reverse_code=self.remove_data_from_file)

    def load_data_from_file(self, apps, schema_editor):
        if os.getenv('DJANGO_CONFIGURATION') != 'Tests' or os.getenv('DJANGO_LOAD_FIXTURES') == 'False':
            return
        if not files(self.package).joinpath(self.fixture).is_file():
            return
        with importlib.resources.path(self.package, self.fixture) as resource:
            content_type_model = apps.get_model('contenttypes', 'contenttype')
            permission_model = apps.get_model('auth', 'permission')
            with open(resource) as stream:
                json_body = json.load(stream)
                for instance in json_body:
                    if instance['model'] != 'auth.permission':
                        continue
                    fields = instance['fields']
                    if 'content_type' not in fields:
                        continue
                    app_label, model = fields['content_type']
                    content_type, _created = content_type_model.objects.get_or_create(
                        app_label=app_label,
                        model=model
                    )
                    permission_model.objects.get_or_create(
                        codename=fields['codename'],
                        name=fields['name'],
                        content_type=content_type,
                    )

    def remove_data_from_file(self, apps, schema_editor):
        pass

    def deconstruct(self):
        kwargs = {
            "package": self.package,
            "fixture": self.fixture,
        }
        if self.reverse_code is not None:
            kwargs["reverse_code"] = self.reverse_code
        if self.atomic is not None:
            kwargs["atomic"] = self.atomic
        if self.hints:
            kwargs["hints"] = self.hints
        return self.__class__.__qualname__, [], kwargs

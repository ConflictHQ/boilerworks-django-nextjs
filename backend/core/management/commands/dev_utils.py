import glob
import json
import logging
import os
from collections import OrderedDict, defaultdict
from datetime import datetime

from core.systems.permissions import AllPermissions
from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core import management
from django.core.management.base import ALL_CHECKS, BaseCommand
from django.db.migrations import Migration, questioner
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from django.db.migrations.state import ProjectState
from django.db.migrations.writer import MigrationWriter
from graphene_django.management.commands.graphql_schema import Command as CommandGraphqlSchema

logger = logging.getLogger(__name__)
settings.INSTALLED_APPS += ('testdata', )


class Command(BaseCommand):
    app_fixtures = OrderedDict([
        ('contenttypes', []),
        ('auth', []),
        ('organization', []),
        ('core', ['organization']),
        ('core_ui', ['core']),
        ('domain_app', ['organization']),
        ('testdata', ['domain_app', 'organization']),

    ])
    help = 'Create Fixtures'

    def add_arguments(self, parser):
        parser.add_argument('--generate_schema', action="store_true", help='Generates project schemas', )
        parser.add_argument('--dumpdata', action="store_true", help='Generate Fixtures', )
        parser.add_argument('--hardreset', action="store_true",
                            help='Deletes db.sqlite3, migrations and load fixtures', )
        parser.add_argument('--loaddata', action="store_true", help='migrations, migrate and load fixtures', )
        parser.add_argument('--gen_perms', action="store_true", help='generate permissions enum', )
        parser.add_argument(
            "--scriptable",
            action="store_true",
            dest="scriptable",
            help=(
                "Divert log output and input prompts to stderr, writing only "
                "paths of generated migration files to stdout."
            ),
        )
        parser.add_argument(
            "--no-header",
            action="store_false",
            dest="include_header",
            help="Do not add header comments to new migration file(s).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Just show what migrations would be made; don't actually write them.",
        )

        parser.add_argument(
            "--add-fixture-migration",
            action="store_true",
            help="Generates migrations for fixtures.",
        )

    def handle(self, *args, **options):
        from config.utils.migrations import LoadFixture
        self.written_files = []
        self.verbosity = options["verbosity"]
        self.scriptable = options["scriptable"]
        self.include_header = options["include_header"]
        self.dry_run = options["dry_run"]
        self.add_fixture_migration = options["add_fixture_migration"]

        if options['gen_perms']:
            self.generate_permissions_enum()
            return

        if options['generate_schema']:
            out = 'static/gql/schema.graphql'
            CommandGraphqlSchema.requires_system_checks = ALL_CHECKS
            management.call_command("graphql_schema",
                                    schema='config.schema.schema',
                                    out=out, )
            try:
                import shutil
                shutil.copy(out, '../frontend/src/utils/schema.graphql')
            except Exception as e:
                logger.warning(f'Warning copying schema.graphql to "./frontend/src/utils/schema.graphql": {e}')

        if options['dumpdata']:
            now = datetime.today().strftime('%Y%m%d_%H%M')
            loader = MigrationLoader(None, ignore_no_migrations=True)
            # Set up autodetector
            autodetector = MigrationAutodetector(
                loader.project_state(),
                ProjectState.from_apps(apps),
                questioner,
            )
            migrations = defaultdict(lambda: [])
            for app_fixture in self.app_fixtures:
                app = app_fixture.replace(".", "_")
                app_directory = 'testdata'
                if not os.path.isdir(app_directory):
                    app_directory = 'core'
                fixture_filename = f"{app}_{now}"

                for old_dump in glob.glob(f"{app_directory}/fixtures/{app}_*.json", recursive=False):
                    logger.warning(f"Removing {old_dump}...")
                    os.remove(old_dump)

                with open(f'{app_directory}/fixtures/{fixture_filename}.json', 'w') as f:
                    logger.info(f'Generating fixture for {app_fixture} to {f.name}')
                    management.call_command(
                        "dumpdata",
                        app_fixture,
                        natural_primary=True,
                        natural_foreign=True,
                        traceback=True,
                        indent=2,
                        stdout=f,
                        verbosity=10)

                    # Make a fake changes() result we can pass to arrange_for_graph
                    operation = LoadFixture(f'{app_directory}.fixtures', f"{fixture_filename}.json")
                    migrations[app_directory].append(operation)
            if self.add_fixture_migration:
                changes = {}
                app_to_migrations = {}
                for app, operations in migrations.items():
                    migration_name = f"load_fixture_dump_{now}"
                    migration = Migration(migration_name, app)
                    migration.operations = operations
                    for app_dependency in self.app_fixtures[app]:
                        migration_dependency = MigrationRecorder.Migration.objects.filter(app=app_dependency).last()
                        migration.dependencies.append((app_dependency, migration_dependency.name))
                    changes[app] = [migration]
                    changes = autodetector.arrange_for_graph(
                        changes=changes,
                        graph=loader.graph,
                        migration_name=migration_name,
                    )
                    app_to_migrations[app] = migration
                self.write_migration_files(changes)

        if options['hardreset']:
            migration_dirs = ['core/migrations/0*.py', 'real_property/migrations/0*.py', ]
            for migration_dir in migration_dirs:
                files = glob.glob(migration_dir)
                for f in files:
                    os.remove(f)

            os.remove('db.sqlite3')

        if options['loaddata'] or options['hardreset']:
            management.call_command("makemigrations")
            management.call_command("migrate")

            for app_fixture in Command.app_fixtures:
                print('>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
                print(app_fixture)
                management.call_command(
                    "loaddata",
                    "--ignorenonexistent",
                    f'core/fixtures/{app_fixture.replace(".", "_")}.json')

    def generate_permissions_enum(self):
        permissions: [Permission] = AllPermissions.load_permissions().permissions.values()
        out = [
            '# file generated using: python manage.py dev_utils --gen_perms ',
            '# do not modify\n',
            'from .permissions import AbstractPermissions\n',
            'from enum import Enum\n\n',
            'class P(AbstractPermissions, Enum):'
        ]
        enums = []
        for p in permissions:
            try:
                model = apps.get_model(app_label=p.content_type.app_label, model_name=p.content_type.model)
                id = AllPermissions.p_to_id(p)
                enum = id.upper().replace('.', '_').replace('-', '_').replace(f'_{model._meta.model_name}'.upper(), '')
                entry = f'    {enum} = "{id}"'
                enums.append(entry)
            except Exception as e:
                p.delete()
                logger.error(f'Error generating permissions enum: {e}')
                logger.error(f'Permission: {p}')

        out.extend(sorted(enums))
        out.append('\n')

        with open('config/roles_gen.py', 'w') as handle:
            handle.write('\n'.join(out))
            logger.info(f'Permissions Generated in: {handle.name}')

    @property
    def log_output(self):
        return self.stderr if self.scriptable else self.stdout

    def log(self, msg):
        self.log_output.write(msg)

    @staticmethod
    def get_relative_path(path):
        try:
            migration_string = os.path.relpath(path)
        except ValueError:
            migration_string = path
        if migration_string.startswith(".."):
            migration_string = path
        return migration_string

    def write_migration_files(self, changes, update_previous_migration_paths=None):
        """
        Take a changes dict and write them out as migration files.
        """
        directory_created = {}
        for app_label, app_migrations in changes.items():
            if self.verbosity >= 1:
                self.log(self.style.MIGRATE_HEADING("Migrations for '%s':" % app_label))
            for migration in app_migrations:
                # Describe the migration
                writer = MigrationWriter(migration, self.include_header)

                if self.verbosity >= 1:
                    # Display a relative path if it's below the current working
                    # directory, or an absolute path otherwise.
                    migration_string = self.get_relative_path(writer.path)
                    self.log("  %s\n" % self.style.MIGRATE_LABEL(migration_string))
                    for operation in migration.operations:
                        self.log("    - %s" % operation.describe())
                    if self.scriptable:
                        self.stdout.write(migration_string)
                if not self.dry_run:
                    # Write the migrations file to the disk.
                    migrations_directory = os.path.dirname(writer.path)
                    if not directory_created.get(app_label):
                        os.makedirs(migrations_directory, exist_ok=True)
                        init_path = os.path.join(migrations_directory, "__init__.py")
                        if not os.path.isfile(init_path):
                            open(init_path, "w").close()
                        # We just do this once per app
                        directory_created[app_label] = True
                    migration_string = writer.as_string()
                    with open(writer.path, "w", encoding="utf-8") as fh:
                        fh.write(migration_string)
                        self.written_files.append(writer.path)
                    if update_previous_migration_paths:
                        prev_path = update_previous_migration_paths[app_label]
                        rel_prev_path = self.get_relative_path(prev_path)
                        if writer.needs_manual_porting:
                            migration_path = self.get_relative_path(writer.path)
                            self.log(
                                self.style.WARNING(
                                    f"Updated migration {migration_path} requires "
                                    f"manual porting.\n"
                                    f"Previous migration {rel_prev_path} was kept and "
                                    f"must be deleted after porting functions manually."
                                )
                            )
                        else:
                            os.remove(prev_path)
                            self.log(f"Deleted {rel_prev_path}")
                elif self.verbosity == 3:
                    # Alternatively, makemigrations --dry-run --verbosity 3
                    # will log the migrations rather than saving the file to
                    # the disk.
                    self.log(
                        self.style.MIGRATE_HEADING(
                            "Full migrations file '%s':" % writer.filename
                        )
                    )
                    self.log(writer.as_string())


class FixtureObjectHistory:
    default_app = 'core'
    apps = {}

    def __new__(cls, app):
        if app in cls.apps:
            return cls.apps[app]
        instance = object.__new__(cls)
        cls.apps[app] = instance
        return instance

    def __init__(self, app):
        self.app = app
        self.directory = app
        if not os.path.isdir(self.directory):
            self.directory = self.default_app
        self.file_format = f"{self.default_app}/fixtures/*.json"
        self.files = sorted(glob.glob(self.file_format))
        self.objects = {}

    def load_objects(self):
        for file in self.files:
            json_file = json.load(file)
            for fixture in json_file:
                key = f"{fixture.model}:{fixture.pk}"
                self.objects[key] = file

    @property
    def next_filename(self):
        return f"{self.directory}/fixtures/{len(self.files):0}_{self.app}.json"

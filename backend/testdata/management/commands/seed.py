"""
Seed management command.

Loads all fixtures from testdata/fixtures/ in numeric order.
Usage:
    python manage.py seed
    python manage.py seed --flush   # truncates non-system tables first
"""
import glob
import os

from django.core import management
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load dev seed fixtures from testdata/fixtures/ in order"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush non-system tables before loading fixtures",
        )

    def handle(self, *args, **options):
        fixtures_dir = os.path.join(os.path.dirname(__file__), "../../fixtures")
        fixtures_dir = os.path.normpath(fixtures_dir)

        fixture_files = sorted(glob.glob(os.path.join(fixtures_dir, "*.json")))
        if not fixture_files:
            self.stdout.write(self.style.WARNING(f"No fixtures found in {fixtures_dir}"))
            return

        if options["flush"]:
            self.stdout.write("Flushing database...")
            management.call_command("flush", "--no-input")

        for fixture_path in fixture_files:
            name = os.path.basename(fixture_path)
            self.stdout.write(f"  Loading {name}...")
            management.call_command(
                "loaddata",
                fixture_path,
                "--ignorenonexistent",
                verbosity=0,
            )

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(fixture_files)} fixture(s)."))

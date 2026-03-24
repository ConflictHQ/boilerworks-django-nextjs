"""
Management command to manage OpenSearch indices.

Usage:
    python manage.py opensearch_index --create    # create index (no-op if exists)
    python manage.py opensearch_index --rebuild   # delete + recreate + reindex all profiles
    python manage.py opensearch_index --delete    # delete index
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Manage OpenSearch indices"

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--create", action="store_true", help="Create index if it does not exist")
        group.add_argument("--rebuild", action="store_true", help="Delete, recreate and reindex all documents")
        group.add_argument("--delete", action="store_true", help="Delete the index")

    def handle(self, *args, **options):
        from core.documents import ProfileDocument

        if options["delete"] or options["rebuild"]:
            if ProfileDocument._index.exists():
                ProfileDocument._index.delete()
                self.stdout.write("  Deleted index 'profiles'.")
            else:
                self.stdout.write("  Index 'profiles' did not exist.")

        if options["create"] or options["rebuild"]:
            ProfileDocument.init()
            self.stdout.write("  Created index 'profiles'.")

        if options["rebuild"]:
            from core.models.user import Profile
            qs = Profile.objects.select_related("user").iterator(chunk_size=500)
            count = 0
            for profile in qs:
                ProfileDocument.index_profile(profile)
                count += 1
            self.stdout.write(self.style.SUCCESS(f"  Indexed {count} profile(s)."))

"""Enable embedding for a Superset dashboard and register it in the app.

Usage:
    python manage.py superset_embed <dashboard id or slug> [--title T] [--order N] [--rls-clause C]

Turns on embedding in Superset (allowed domains: SUPERSET_EMBED_ALLOWED_DOMAINS)
and creates or updates the matching SupersetDashboard row. Safe to re-run.
"""
from core.models import SupersetDashboard
from core.utils.api.superset_rest_client import SupersetError, SupersetRestClient
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Enable embedding for a Superset dashboard and register it as a SupersetDashboard'

    def add_arguments(self, parser):
        parser.add_argument('dashboard', help='Superset dashboard id or slug')
        parser.add_argument('--title', help="Title in the app (defaults to the dashboard's title in Superset)")
        parser.add_argument('--order', type=int, help='Position in the analytics page (lowest first)')
        parser.add_argument('--rls-clause', help='Row-level security clause for guest tokens')

    def handle(self, *args, **options):
        try:
            embedded_id, superset_title = SupersetRestClient().enable_embedding(
                options['dashboard'], settings.SUPERSET_EMBED_ALLOWED_DOMAINS,
            )
        except SupersetError as error:
            raise CommandError(str(error)) from error

        dashboard = SupersetDashboard.objects.filter(embedded_id=embedded_id).first() or SupersetDashboard(
            embedded_id=embedded_id,
        )
        dashboard.title = options['title'] or dashboard.title or superset_title
        if options['order'] is not None:
            dashboard.order = options['order']
        if options['rls_clause'] is not None:
            dashboard.rls_clause = options['rls_clause']
        dashboard.deleted_at = None
        dashboard.deleted_by = None
        dashboard.save()

        self.stdout.write(self.style.SUCCESS(f'Embedded "{dashboard.title}" ({embedded_id}) as {dashboard.guid}'))

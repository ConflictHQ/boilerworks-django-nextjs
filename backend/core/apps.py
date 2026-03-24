import logging
import os

from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from core.documents import register_profile_signals, setup_opensearch
        setup_opensearch()
        register_profile_signals()

        from config.health_opensearch import OpenSearchHealthCheck
        from health_check.plugins import plugin_dir
        plugin_dir.register(OpenSearchHealthCheck)

        from config.telemetry import setup as telemetry_setup
        from django.conf import settings
        telemetry_setup(
            service_name="boilerworks",
            service_version=settings.VERSION,
            environment=settings.CONFIGURATION,
            is_local=settings.IS_LOCAL,
        )

        post_migrate.connect(self.register_objects, sender=self)

        # Register core file exporters
        self._register_file_exporters()

        # Register core processors
        self._register_processors()

    @staticmethod
    def _register_file_exporters():
        """Register core file exporters."""
        from core.utils.file_export_registry import register_file_exporter
        from core.utils.file_processor.file_export import ChatHistory

        register_file_exporter('rocket-channel-history', ChatHistory)

    @staticmethod
    def _register_processors():
        """Register core data processors."""
        from core.models.process import EntityType
        from core.utils.file_processor.permissions_processor import PermissionsProcessor
        from core.utils.file_processor.site_label_processor import SiteLabelProcessor
        from core.utils.processor_registry import register_processor

        register_processor(EntityType.SITE_LABEL, SiteLabelProcessor)
        register_processor(EntityType.PERMISSIONS, PermissionsProcessor)

    @classmethod
    def register_objects(cls, sender, **kwargs):
        from django.contrib.auth.models import User
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@boilerworks.dev', os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme'))
        except Exception:
            logging.info("Unable to create admin user.")

        from .emails import Emails
        Emails.register(sender)

        from .models.interval import Intervals
        Intervals.register(sender)

        from .models.authorization.actions import SharedFilePermissions
        SharedFilePermissions.register(sender)

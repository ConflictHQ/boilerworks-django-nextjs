"""List enabled/disabled platform features with their status.

Usage:
    python manage.py features
"""
from django.core.management.base import BaseCommand

from config.features import FEATURE_APPS, FEATURE_DEFAULTS, Feature, is_enabled


class Command(BaseCommand):
    help = "List platform feature toggles and their status"

    def handle(self, *args, **options):
        self.stdout.write('\nBoilerworks Feature Toggles')
        self.stdout.write('=' * 50)

        for feature in Feature:
            enabled = is_enabled(feature)
            env_key, default = FEATURE_DEFAULTS[feature]
            apps = FEATURE_APPS.get(feature, [])
            status = self.style.SUCCESS('ON ') if enabled else self.style.ERROR('OFF')
            apps_str = f'  apps: {", ".join(apps)}' if apps else ''

            self.stdout.write(
                f'  {status}  {feature.value:<25s}  env: {env_key}{apps_str}'
            )

        self.stdout.write('')
        self.stdout.write('To toggle a feature, set the environment variable:')
        self.stdout.write('  FEATURE_FORMS=false  (disable forms)')
        self.stdout.write('  FEATURE_WORKFLOWS=true  (enable workflows)')
        self.stdout.write('')
        self.stdout.write('Docker compose profiles:')
        self.stdout.write('  docker compose --profile search --profile storage --profile monitoring up -d')
        self.stdout.write('')

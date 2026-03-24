"""Boilerworks feature toggle system.

Controls which platform features are enabled. Disabled features:
- Are removed from INSTALLED_APPS
- Are excluded from the GraphQL schema
- Have their Docker services skipped (via compose profiles)
- Have their Celery tasks unregistered
- Have their signals disconnected

Usage:
    from config.features import is_enabled, Feature

    if is_enabled(Feature.FORMS):
        # do form stuff

    # In settings.py:
    INSTALLED_APPS = get_enabled_apps(INSTALLED_APPS)

    # In schema.py:
    query_bases, mutation_bases = get_enabled_schema_classes()
"""
import logging
import os
from enum import Enum

logger = logging.getLogger(__name__)


def _env_bool(key, default=True):
    return os.environ.get(key, str(default)).lower() in ('true', '1', 'yes')


class Feature(str, Enum):
    """Platform features that can be toggled on/off."""
    FORMS = 'forms'
    WORKFLOWS = 'workflows'
    CELERY = 'celery'
    TEMPORAL = 'temporal'
    OPENSEARCH = 'opensearch'
    METABASE = 'metabase'
    ROCKETCHAT = 'rocketchat'
    PUSH_NOTIFICATIONS = 'push_notifications'
    FILE_UPLOADS = 'file_uploads'
    RULE_ENGINE = 'rule_engine'


# Feature → environment variable → default
FEATURE_DEFAULTS = {
    Feature.FORMS: ('FEATURE_FORMS', True),
    Feature.WORKFLOWS: ('FEATURE_WORKFLOWS', True),
    Feature.CELERY: ('FEATURE_CELERY', True),
    Feature.TEMPORAL: ('FEATURE_TEMPORAL', False),
    Feature.OPENSEARCH: ('FEATURE_OPENSEARCH', True),
    Feature.METABASE: ('FEATURE_METABASE', True),
    Feature.ROCKETCHAT: ('FEATURE_ROCKETCHAT', True),
    Feature.PUSH_NOTIFICATIONS: ('FEATURE_PUSH_NOTIFICATIONS', True),
    Feature.FILE_UPLOADS: ('FEATURE_FILE_UPLOADS', True),
    Feature.RULE_ENGINE: ('FEATURE_RULE_ENGINE', True),
}

# Feature → Django apps that belong to it
FEATURE_APPS = {
    Feature.FORMS: ['forms'],
    Feature.WORKFLOWS: ['workflows'],
    Feature.CELERY: ['django_celery_results', 'django_celery_beat'],
    Feature.PUSH_NOTIFICATIONS: ['pushnotif'],
    Feature.RULE_ENGINE: ['core_rule_engine'],
    Feature.OPENSEARCH: [],  # opensearch is a service, not a Django app
    Feature.METABASE: [],
    Feature.ROCKETCHAT: [],
    Feature.FILE_UPLOADS: [],
    Feature.WORKFLOWS: [],
    Feature.TEMPORAL: [],
}

# Feature → GraphQL schema module (app_label.schema)
FEATURE_SCHEMA_MODULES = {
    Feature.FORMS: 'forms.schema',
    Feature.WORKFLOWS: 'workflows.schema',
    Feature.PUSH_NOTIFICATIONS: 'pushnotif.schema',
}


def is_enabled(feature: Feature) -> bool:
    """Check if a feature is enabled via environment variable."""
    env_key, default = FEATURE_DEFAULTS[feature]
    return _env_bool(env_key, default)


def get_enabled_features() -> dict[Feature, bool]:
    """Get all features with their enabled/disabled status."""
    return {f: is_enabled(f) for f in Feature}


def get_disabled_apps() -> set[str]:
    """Get the set of Django app labels that should be removed from INSTALLED_APPS."""
    disabled = set()
    for feature, apps in FEATURE_APPS.items():
        if not is_enabled(feature):
            disabled.update(apps)
    return disabled


def filter_installed_apps(apps: list[str]) -> list[str]:
    """Remove disabled feature apps from INSTALLED_APPS."""
    disabled = get_disabled_apps()
    if disabled:
        logger.info(f'Disabled feature apps: {disabled}')
    return [app for app in apps if app not in disabled]


def get_enabled_schema_classes():
    """Dynamically build Query and Mutation base classes from enabled features.

    Returns (query_bases, mutation_bases) tuples of classes to inherit from.
    """
    query_bases = []
    mutation_bases = []

    for feature, module_path in FEATURE_SCHEMA_MODULES.items():
        if not is_enabled(feature):
            logger.info(f'Schema: skipping disabled feature {feature.value}')
            continue
        try:
            import importlib
            mod = importlib.import_module(module_path)
            if hasattr(mod, 'Query'):
                query_bases.append(mod.Query)
            if hasattr(mod, 'Mutation'):
                mutation_bases.append(mod.Mutation)
        except ImportError as e:
            logger.warning(f'Schema: could not import {module_path}: {e}')

    return query_bases, mutation_bases

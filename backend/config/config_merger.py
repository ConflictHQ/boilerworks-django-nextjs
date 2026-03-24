"""
ConfigMerger - Discovers and merges configuration from domain apps.

This module enables domain apps to integrate with boilerworks
infrastructure without creating hard dependencies. Domain apps declare their
configuration in boilerworks_config/settings.py files.

Usage:
    from config.config_merger import ConfigMerger

    # In settings.py
    config_merger = ConfigMerger(BASE_DIR)
    config_merger.discover()

    # Merge INSTALLED_APPS
    INSTALLED_APPS.extend(config_merger.get_installed_apps())

    # Merge MIDDLEWARE
    MIDDLEWARE.extend(config_merger.get_middleware())

    # Merge custom settings
    config_merger.merge_settings(globals())
"""

import importlib.util
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConfigMerger:
    """
    Discovers and merges configuration from domain apps.

    Scans for apps with boilerworks_config/settings.py and merges their
    configuration into Django settings.
    """

    def __init__(self, base_dir: Path):
        """
        Initialize ConfigMerger.

        Args:
            base_dir: Path to the backend directory (where apps are located)
        """
        self.base_dir = Path(base_dir)
        self.domain_configs: Dict[str, Any] = {}
        self.discovered_apps: List[str] = []

    def discover(self) -> List[str]:
        """
        Discover all apps with boilerworks_config/settings.py.

        Returns:
            List of discovered app names
        """
        if not self.base_dir.exists():
            logger.error(f'Base directory does not exist: {self.base_dir}')
            return []

        for item in os.listdir(self.base_dir):
            app_path = self.base_dir / item

            # Skip non-directories
            if not app_path.is_dir():
                continue

            # Skip special directories
            if item.startswith('.') or item.startswith('_'):
                continue

            settings_file = app_path / 'boilerworks_config' / 'settings.py'

            if settings_file.exists():
                try:
                    config_module = self._load_config_module(item, settings_file)
                    self.domain_configs[item] = config_module
                    self.discovered_apps.append(item)
                    logger.info(f'✓ Discovered domain app: {item}')
                except Exception as e:
                    logger.error(f'✗ Failed to load config for {item}: {e}')

        if self.discovered_apps:
            logger.info(f'Loaded {len(self.discovered_apps)} domain app(s): {", ".join(self.discovered_apps)}')
        else:
            logger.info('No domain apps with boilerworks_config found')

        return self.discovered_apps

    def _load_config_module(self, app_name: str, settings_file: Path):
        """
        Dynamically load a settings.py module.

        Args:
            app_name: Name of the app
            settings_file: Path to settings.py file

        Returns:
            Loaded module object
        """
        module_name = f'{app_name}.boilerworks_config.settings'

        # Load module using importlib
        spec = importlib.util.spec_from_file_location(module_name, settings_file)
        if spec is None or spec.loader is None:
            raise ImportError(f'Cannot load spec for {module_name}')

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        return module

    def get_installed_apps(self) -> List[str]:
        """
        Collect INSTALLED_APPS from all domain configs.

        Returns:
            List of app names to add to INSTALLED_APPS
        """
        apps = []
        for app_name, config in self.domain_configs.items():
            if hasattr(config, 'INSTALLED_APPS'):
                config_apps = config.INSTALLED_APPS
                if isinstance(config_apps, (list, tuple)):
                    apps.extend(config_apps)
                    logger.debug(f'  {app_name}: Added {len(config_apps)} app(s) to INSTALLED_APPS')
        return apps

    def get_middleware(self) -> List[str]:
        """
        Collect MIDDLEWARE from all domain configs.

        Returns:
            List of middleware classes to add to MIDDLEWARE
        """
        middleware = []
        for app_name, config in self.domain_configs.items():
            if hasattr(config, 'MIDDLEWARE'):
                config_middleware = config.MIDDLEWARE
                if isinstance(config_middleware, (list, tuple)):
                    middleware.extend(config_middleware)
                    logger.debug(f'  {app_name}: Added {len(config_middleware)} middleware(s)')
        return middleware

    def get_graphql_schemas(self) -> Dict[str, List[str]]:
        """
        Collect GraphQL schema classes from all domain configs.

        Returns:
            Dictionary with 'query' and 'mutation' lists containing schema class paths
        """
        schemas: Dict[str, List[str]] = {'query': [], 'mutation': []}

        for app_name, config in self.domain_configs.items():
            if hasattr(config, 'GRAPHQL_SCHEMA'):
                schema_config = config.GRAPHQL_SCHEMA
                if isinstance(schema_config, dict):
                    if 'query' in schema_config:
                        schemas['query'].append(schema_config['query'])
                        logger.debug(f'  {app_name}: Added GraphQL Query')
                    if 'mutation' in schema_config:
                        schemas['mutation'].append(schema_config['mutation'])
                        logger.debug(f'  {app_name}: Added GraphQL Mutation')

        return schemas

    def get_url_patterns(self) -> List[Dict[str, str]]:
        """
        Collect URL configuration from all domain configs.

        Returns:
            List of URL pattern configurations
        """
        url_patterns = []

        for app_name, config in self.domain_configs.items():
            if hasattr(config, 'URL_PATTERNS'):
                url_config = config.URL_PATTERNS
                if isinstance(url_config, dict):
                    url_patterns.append(url_config)
                    logger.debug(f'  {app_name}: Added URL patterns')

        return url_patterns

    def merge_settings(self, settings_dict: Dict[str, Any]) -> None:
        """
        Merge custom settings from domain configs into Django settings.

        This merges any UPPERCASE variables from domain configs that aren't
        already handled by specific methods (INSTALLED_APPS, MIDDLEWARE, etc.).

        Args:
            settings_dict: Django settings dictionary (usually globals())
        """
        # Settings to skip (handled by other methods)
        skip_settings = {
            'INSTALLED_APPS',
            'MIDDLEWARE',
            'GRAPHQL_SCHEMA',
            'URL_PATTERNS',
        }

        merged_count = 0

        for app_name, config in self.domain_configs.items():
            for key in dir(config):
                # Only process uppercase variables (Django convention)
                if not key.isupper():
                    continue

                # Skip handled settings
                if key in skip_settings:
                    continue

                # Skip private/magic variables
                if key.startswith('_'):
                    continue

                # Merge setting
                value = getattr(config, key)
                settings_dict[key] = value
                merged_count += 1
                logger.debug(f'  {app_name}: Merged setting {key}')

        if merged_count > 0:
            logger.info(f'Merged {merged_count} custom setting(s) from domain apps')

    def get_config(self, app_name: str) -> Optional[Any]:
        """
        Get the configuration module for a specific app.

        Args:
            app_name: Name of the app

        Returns:
            Configuration module or None if not found
        """
        return self.domain_configs.get(app_name)

    def has_config(self, app_name: str) -> bool:
        """
        Check if an app has a configuration.

        Args:
            app_name: Name of the app

        Returns:
            True if app has configuration, False otherwise
        """
        return app_name in self.domain_configs

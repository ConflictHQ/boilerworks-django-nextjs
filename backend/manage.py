#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import importlib.util
import logging
import os
import sys
import types

# Python 3.12 removed the `imp` module. snapshottest 0.6.0 still imports it.
# Inject a minimal shim so tests can run until snapshottest is updated.
if 'imp' not in sys.modules:
    _imp = types.ModuleType('imp')

    def _load_source(name, pathname, file=None):
        spec = importlib.util.spec_from_file_location(name, pathname)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    _imp.load_source = _load_source
    sys.modules['imp'] = _imp

logger = logging.getLogger(__name__)
if sys.argv[0] and sys.argv[0].find('django_test_manage.py') >= 0:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_plain')
    os.environ.setdefault("DJANGO_CONFIGURATION", "Tests")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    logger.warning(f'DJANGO_SETTINGS_MODULE: {os.environ["DJANGO_SETTINGS_MODULE"]}')

    try:
        from django.core.management import execute_from_command_line
        execute_from_command_line(sys.argv)
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc


if __name__ == '__main__':
    main()

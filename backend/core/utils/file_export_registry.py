"""
File Export Registry - Allows domain apps to register custom file exporters.

This registry pattern allows domain apps to register their
custom file export implementations without creating hard dependencies in core.

Usage:
    # In a domain app's apps.py ready() method:
    from core.utils.file_export_registry import register_file_exporter
    from myapp.exporters import MyReport

    register_file_exporter('my-report', MyReport)

    # In core/views.py:
    from core.utils.file_export_registry import get_file_exporter

    exporter_class = get_file_exporter('my-report')
    if exporter_class:
        exporter = exporter_class()
"""

import logging
from typing import Dict, Optional, Type

logger = logging.getLogger(__name__)

# Global registry for file exporters
_file_exporters: Dict[str, Type] = {}


def register_file_exporter(name: str, exporter_class: Type) -> None:
    """
    Register a file exporter class.

    Args:
        name: Unique name for the exporter (e.g., 'alliance-report')
        exporter_class: FileExport subclass
    """
    if name in _file_exporters:
        logger.warning(f'File exporter "{name}" is already registered, overwriting')

    _file_exporters[name] = exporter_class
    logger.debug(f'Registered file exporter: {name} -> {exporter_class.__name__}')


def get_file_exporter(name: str) -> Optional[Type]:
    """
    Get a file exporter class by name.

    Args:
        name: Name of the exporter

    Returns:
        Exporter class or None if not found
    """
    return _file_exporters.get(name)


def list_file_exporters() -> list[str]:
    """
    List all registered file exporter names.

    Returns:
        List of exporter names
    """
    return list(_file_exporters.keys())


def clear_registry() -> None:
    """
    Clear all registered file exporters.

    This is mainly useful for testing.
    """
    _file_exporters.clear()

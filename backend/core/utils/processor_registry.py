"""
Processor Registry - Allows domain apps to register custom file processors.

This registry pattern allows domain apps to register their
custom data processor implementations without creating hard dependencies in core.

Usage:
    # In a domain app's apps.py ready() method:
    from core.utils.processor_registry import register_processor
    from core.models.process import EntityType
    from myapp.processors import MyProcessor

    register_processor(EntityType.MY_ENTITY, MyProcessor)

    # In core/systems/process_system.py:
    from core.utils.processor_registry import get_processor

    processor_class = get_processor(EntityType.MY_ENTITY)
    if processor_class:
        processor = processor_class()
"""

import logging
from typing import Dict, Optional, Type

logger = logging.getLogger(__name__)

# Global registry for processors
_processors: Dict[str, Type] = {}


def register_processor(entity_type, processor_class: Type) -> None:
    """
    Register a data processor class for an entity type.

    Args:
        entity_type: EntityType enum value
        processor_class: Processor subclass
    """
    entity_type_str = str(entity_type)

    if entity_type_str in _processors:
        logger.warning(f'Processor for "{entity_type_str}" is already registered, overwriting')

    _processors[entity_type_str] = processor_class
    logger.debug(f'Registered processor: {entity_type_str} -> {processor_class.__name__}')


def get_processor(entity_type) -> Optional[Type]:
    """
    Get a processor class for an entity type.

    Args:
        entity_type: EntityType enum value

    Returns:
        Processor class or None if not found
    """
    entity_type_str = str(entity_type)
    return _processors.get(entity_type_str)


def list_processors() -> list[str]:
    """
    List all registered processor entity types.

    Returns:
        List of entity type strings
    """
    return list(_processors.keys())


def clear_registry() -> None:
    """
    Clear all registered processors.

    This is mainly useful for testing.
    """
    _processors.clear()

"""
Broadcast Handler Registry - Allows domain apps to register broadcast handlers.

This registry pattern allows domain apps to register their
broadcast handling logic without creating hard dependencies in pushnotif.

Usage:
    # In a domain app's apps.py ready() method:
    from pushnotif.broadcast_registry import register_broadcast_handler
    from myapp.handlers import my_broadcast_handler

    register_broadcast_handler(my_broadcast_handler)

    # In pushnotif/service.py:
    from pushnotif.broadcast_registry import get_broadcast_handlers

    for handler in get_broadcast_handlers():
        handler(sender, recipient, instance, notification_type, template_id, on_behalf_of)
"""

import logging
from typing import Callable, List

logger = logging.getLogger(__name__)

# Global registry for broadcast handlers
# Handler signature: (sender, recipient, instance, notification_type, template_id, on_behalf_of) -> None
_broadcast_handlers: List[Callable] = []


def register_broadcast_handler(handler: Callable) -> None:
    """
    Register a broadcast handler function.

    Handler signature should be:
        def handler(sender, recipient, instance, notification_type, template_id, on_behalf_of=None):
            # Handle broadcast logic
            pass

    Args:
        handler: Callable that handles broadcast notifications
    """
    if handler in _broadcast_handlers:
        logger.warning(f'Broadcast handler {handler.__name__} is already registered')
        return

    _broadcast_handlers.append(handler)
    logger.debug(f'Registered broadcast handler: {handler.__name__}')


def get_broadcast_handlers() -> List[Callable]:
    """
    Get all registered broadcast handlers.

    Returns:
        List of broadcast handler functions
    """
    return _broadcast_handlers.copy()


def clear_registry() -> None:
    """
    Clear all registered broadcast handlers.

    This is mainly useful for testing.
    """
    _broadcast_handlers.clear()

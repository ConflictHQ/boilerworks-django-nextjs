"""
Organization signals.

Signals allow domain apps to respond to organization events without
creating hard dependencies in the organization package.
"""

from django.dispatch import Signal

# Signal sent when an organization member's activation status changes
# Provides: sender (class), instance (OrganizationMember), is_active (bool), user_id (str)
organization_member_activation_changed = Signal()

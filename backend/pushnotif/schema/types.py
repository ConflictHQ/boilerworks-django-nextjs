from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from core.schema.common import permission_filtered_queryset
from pushnotif.models import (
    DeliveryMethod,
    DeliveryMethodNotificationTemplate,
    DeviceToken,
    EmailNotification,
    NotificationConfig,
    NotificationTemplate,
    PushNotification,
    SMSNotification,
)


# ---------------------------------------------------------------------------
# Simple notification types (direct model mappings)
# ---------------------------------------------------------------------------

@strawberry_django.type(EmailNotification)
class EmailNotificationType:
    title: str
    message: str


@strawberry_django.type(SMSNotification)
class SMSNotificationType:
    title: str
    message: str


@strawberry_django.type(PushNotification)
class PushNotificationType:
    title: str
    message: str


# ---------------------------------------------------------------------------
# Template / config types
# ---------------------------------------------------------------------------

@strawberry_django.type(NotificationTemplate)
class NotificationTemplateType:
    name: str
    display_name: str
    member: Optional[str]


@strawberry_django.type(DeliveryMethod)
class DeliveryMethodType:
    """Delivery method with permission-based queryset filtering."""
    name: str
    display_name: str

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)


@strawberry_django.type(DeviceToken)
class DeviceTokenType:
    """Device token with permission-based queryset filtering."""
    delivery_method: DeliveryMethodType
    name: str

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)


@strawberry_django.type(NotificationConfig)
class NotificationConfigType:
    """Notification config scoped to the authenticated user's profile."""
    is_enabled: bool

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        if not info.context.user.is_authenticated:
            return NotificationConfig.objects.none()
        return queryset.filter(profile=info.context.user.profile)


@strawberry_django.type(DeliveryMethodNotificationTemplate)
class DeliveryMethodNotificationTemplateType:
    """Delivery-method/template junction with per-user notification config resolver."""
    delivery_method: DeliveryMethodType
    notification_template: NotificationTemplateType
    always_send_notification: bool
    never_send_notification: bool

    @strawberry_django.field
    def user_notification_config(self, info: Info) -> Optional[NotificationConfigType]:
        """Return the current user's config for this template, or a default."""
        user_profile = info.context.user.profile
        config = NotificationConfig.objects.filter(
            profile=user_profile,
            delivery_method_template=self,
        ).first()

        if config:
            return config

        return NotificationConfig(
            profile=user_profile,
            delivery_method_template=self,
            is_enabled=True,
        )

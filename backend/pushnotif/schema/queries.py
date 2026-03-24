from __future__ import annotations

import strawberry
import strawberry_django
from strawberry.types import Info

from pushnotif.models import DeliveryMethodNotificationTemplate, DeviceToken
from pushnotif.schema.types import (
    DeliveryMethodNotificationTemplateType,
    DeviceTokenType,
)


@strawberry.type
class Query:

    @strawberry_django.field
    def devices(self, info: Info) -> list[DeviceTokenType]:
        """Get all devices registered for the current user."""
        if DeviceToken.p('model').view.by(info.context.user):
            return DeviceToken.objects.filter(recipient=info.context.user).all()
        return []

    @strawberry_django.field
    def delivery_method_templates(self, info: Info) -> list[DeliveryMethodNotificationTemplateType]:
        """Get all delivery method templates."""
        return DeliveryMethodNotificationTemplate.objects.all()

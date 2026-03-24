import logging

import graphene

from ...models import DeliveryMethodNotificationTemplate, DeviceToken, NotificationConfig
from ..types.device_token import DeviceTokenType

logger = logging.getLogger(__name__)
from ..types import *  # noqa


class Query(
    graphene.ObjectType
):

    devices = graphene.List(
        DeviceTokenType,
        description="Get all devices registered for current user."
    )

    delivery_method_templates = graphene.List(
        DeliveryMethodNotificationTemplateType,
        description="Get all delivery method templates."
    )

    @staticmethod
    def resolve_devices(root, info):
        if DeviceToken.p('model').view.by(info.context.user):
            return DeviceToken.objects.filter(recipient=info.context.user).all()
        return []

    @staticmethod
    def resolve_delivery_method_templates(root, info):
        return DeliveryMethodNotificationTemplate.objects.all()

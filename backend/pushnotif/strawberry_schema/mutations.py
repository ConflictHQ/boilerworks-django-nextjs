from __future__ import annotations

import logging
from enum import Enum
from typing import Optional

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from core.strawberry_schema.common import GlobalIDUtils, MutationResult, unpack_nested_errors
from core.strawberry_schema.mutations.base import restricted_serializer_mutate

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

@strawberry.enum
class DeviceTokenOperationEnum(Enum):
    SUBSCRIBE = 'Subscribe'
    UNSUBSCRIBE = 'Unsubscribe'


@strawberry.enum
class DeliveryMethodEnum(Enum):
    ANDROID = 'Android'
    IOS = 'IOS'
    SMS = 'SMS'
    EMAIL = 'Email'
    WEBAPP = 'Web Application'


# ---------------------------------------------------------------------------
# Input types
# ---------------------------------------------------------------------------

@strawberry.input
class DeviceTokenInput:
    device_token: str
    name: Optional[str] = None
    delivery_method_id: Optional[DeliveryMethodEnum] = None
    device_operation: Optional[DeviceTokenOperationEnum] = None


@strawberry.input
class NotificationConfigInput:
    delivery_method_template: strawberry.ID
    is_enabled: bool


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@strawberry.type
class Mutation:

    @strawberry.mutation
    def device_token(self, info: Info, input: DeviceTokenInput) -> MutationResult:
        """Subscribe or unsubscribe a device token for push notifications."""
        from pushnotif.models import DeviceToken
        from pushnotif.serializers.device_token import DeviceTokenSerializer

        user = info.context.user

        # Handle UNSUBSCRIBE — delete the token
        if (
            input.device_operation is not None
            and input.device_operation.name == DeviceTokenOperationEnum.UNSUBSCRIBE.name
        ):
            DeviceToken.p('model').delete.check(user)
            instance = DeviceToken.objects.filter(device_token=input.device_token).first()
            if instance:
                instance.delete()
            return MutationResult.success()

        # Build serializer data for subscribe/update
        data: dict = {
            'device_token': input.device_token,
            'recipient_id': user.id,
        }
        if input.name is not None:
            data['name'] = input.name
        if input.delivery_method_id is not None:
            data['delivery_method_id'] = input.delivery_method_id.name

        # Look up existing token to decide create vs update
        instance = DeviceToken.objects.filter(device_token=input.device_token).first()
        if instance is None:
            data['created_by_id'] = user.id
            data['recipient_id'] = user.id
        else:
            data['updated_by_id'] = user.id

        return restricted_serializer_mutate(
            serializer_class=DeviceTokenSerializer,
            model_class=DeviceToken,
            info=info,
            data=data,
            instance=instance,
        )

    @strawberry.mutation
    def notification_config(self, info: Info, input: NotificationConfigInput) -> MutationResult:
        """Create or update a user's notification preference for a delivery method template."""
        from pushnotif.models import NotificationConfig
        from pushnotif.serializers.notification_config import NotificationConfigSerializer

        user = info.context.user

        # Decode the relay global ID to a raw PK
        pk = GlobalIDUtils.get_pk_flexible(input.delivery_method_template)
        if pk is None:
            raise GraphQLError(f'Invalid delivery_method_template ID: {input.delivery_method_template}')

        # Upsert: look up existing config for (profile, delivery_method_template)
        instance = NotificationConfig.objects.filter(
            profile=user.profile,
            delivery_method_template=pk,
        ).first()

        data = {
            'delivery_method_template': pk,
            'is_enabled': input.is_enabled,
        }

        return restricted_serializer_mutate(
            serializer_class=NotificationConfigSerializer,
            model_class=NotificationConfig,
            info=info,
            data=data,
            instance=instance,
        )

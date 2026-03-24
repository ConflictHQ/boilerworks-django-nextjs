import graphene
from core.schema import DjangoObjectTypeUtils, MetaNode
from graphene_django import DjangoObjectType
from pushnotif.models import (
    DeliveryMethodNotificationTemplate,
    EmailNotification,
    NotificationConfig,
    NotificationTemplate,
    PushNotification,
    SMSNotification,
)
from pushnotif.schema.types.delivery_method import DeliveryMethodType


class EmailNotificationType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = EmailNotification


class SMSNotificationType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = SMSNotification


class PushNotificationType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = PushNotification


class NotificationTemplateType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = NotificationTemplate
        fields = ['name', 'display_name', 'member']


class DeliveryMethodNotificationTemplateType(DjangoObjectType, DjangoObjectTypeUtils):
    delivery_method = graphene.Field(DeliveryMethodType)
    notification_template = graphene.Field(NotificationTemplateType)
    user_notification_config = graphene.Field('pushnotif.schema.types.notification_config.NotificationConfigType')

    class Meta(MetaNode):
        model = DeliveryMethodNotificationTemplate
        fields = ['delivery_method', 'notification_template', 'always_send_notification', 'never_send_notification']

    def resolve_user_notification_config(self, info):
        user_profile = info.context.user.profile
        config = NotificationConfig.objects.filter(
            profile=user_profile,
            delivery_method_template=self
        ).first()

        if config:
            return config
        else:
            return NotificationConfig(
                profile=user_profile,
                delivery_method_template=self,
                is_enabled=True
            )

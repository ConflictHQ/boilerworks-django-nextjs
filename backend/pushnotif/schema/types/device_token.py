import graphene
from core.schema import DjangoObjectTypeUtils, DjangoPermissionFilterMixin, MetaNode
from graphene_django import DjangoObjectType
from pushnotif.models import DeviceToken
from pushnotif.schema.types.delivery_method import DeliveryMethodType


class DeviceTokenType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    delivery_method = graphene.Field(DeliveryMethodType)

    class Meta(MetaNode):
        model = DeviceToken
        fields = ['delivery_method', 'name']

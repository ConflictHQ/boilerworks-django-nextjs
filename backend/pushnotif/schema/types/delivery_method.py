from core.schema import DjangoObjectTypeUtils, DjangoPermissionFilterMixin, MetaNode
from graphene_django import DjangoObjectType
from pushnotif.models import DeliveryMethod


class DeliveryMethodType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    class Meta(MetaNode):
        model = DeliveryMethod
        fields = ['name', 'display_name']

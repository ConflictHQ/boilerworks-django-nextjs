from graphene_django import DjangoObjectType

from ..models import Address
from .common import DjangoObjectTypeUtils, MetaNode


class AddressType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = Address

    @staticmethod
    def resolve_address_line_one(root: Address, info):
        if Address.p('address_line_one').view.by(info.context.user):
            return root.address_line_one
        return ""

    @staticmethod
    def resolve_address_line_two(root: Address, info):
        if Address.p('address_line_two').view.by(info.context.user):
            return root.address_line_two
        return ""

    @staticmethod
    def resolve_city(root: Address, info):
        if Address.p('city').view.by(info.context.user):
            return root.city
        return ""

    @staticmethod
    def resolve_state(root: Address, info):
        if Address.p('state').view.by(info.context.user):
            return root.state
        return ""

    @staticmethod
    def resolve_street(root: Address, info):
        if Address.p('street').view.by(info.context.user):
            return root.street
        return ""

    @staticmethod
    def resolve_zipcode(root: Address, info):
        if Address.p('zipcode').view.by(info.context.user):
            return root.zipcode
        return ""

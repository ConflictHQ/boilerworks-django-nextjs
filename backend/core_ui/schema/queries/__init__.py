import graphene
from core_ui.models import Component
from graphene_django.debug import DjangoDebug
from graphene_django.filter import DjangoFilterConnectionField

from ..types.component import ComponentType


class Query(graphene.ObjectType):
    components = DjangoFilterConnectionField(ComponentType)
    component = graphene.Field(ComponentType, slug=graphene.String())

    debug = graphene.Field(DjangoDebug, name="_ui_debug")

    @staticmethod
    def resolve_components(root, info, **kwargs):
        return Component.objects.with_view_permission_info(info)

    @staticmethod
    def resolve_component(root, info, slug=None, **kwargs):
        return Component.objects \
            .with_view_permission_info(info) \
            .filter(slug=slug) \
            .first()

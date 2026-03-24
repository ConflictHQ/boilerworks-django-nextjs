from typing import Optional

from core.dataloaders import DataLoaderContext, dataloader, dataloader_cache
from core.schema.common import DjangoObjectTypeUtils, MetaNode
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphql import GraphQLResolveInfo
from organization.models import Organization
from organization.models.organization import OrganizationMember


@dataloader_cache
class OrganizationCache:
    """
    Cache for Organizations

    We keep this model in memory since it is used too heavily.
    """

    def __init__(self, context: DataLoaderContext):
        self.context = context
        self.organizations: dict[int, Organization] = {
            organization.id: organization
            for organization in Organization.objects.all()
        }

    def __getitem__(self, item: int) -> Optional[Organization]:
        return self.organizations.get(item)


class OrganizationType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = Organization


class OrganizationMemberType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = OrganizationMember

    def resolve_organization(self: OrganizationMember, info: GraphQLResolveInfo):
        cache = OrganizationCache(info.context)
        return cache[self.organization_id]

    @dataloader
    @staticmethod
    def load_user_by_id(_context: DataLoaderContext, users_ids: list[int], **_kwargs):
        for user in get_user_model().objects.filter(id__in=users_ids):
            yield user.id, user

    def resolve_member(self: OrganizationMember, info: GraphQLResolveInfo):
        return info.context.load_user_by_id(self.member_id)


from graphene_django import DjangoConnectionField

from .mutations import *  # noqa
from .organization import *  # noqa


class Mutation(graphene.ObjectType):
    organization_mutation = OrganizationMutation.Field()
    upsert_organization = UpsertOrganizationMutation.Field()
    organization_member_status = OrganizationMemberStatusMutation.Field()


class Query(graphene.ObjectType):
    organization = graphene.Field(OrganizationType, id=graphene.ID())
    organizations = DjangoConnectionField(OrganizationType, query=graphene.String(), connected=graphene.Boolean())
    members = DjangoConnectionField(OrganizationMemberType, query=graphene.String())

    @staticmethod
    def resolve_organizations(root, info, query='', *args, **kwargs):
        qs = Organization.objects.filter()
        if query:
            query = [q for q in query.split(' ') if q]
            for q in query:
                qs = qs.filter(search__icontains=q)

        return qs

    @staticmethod
    def resolve_organization(root, info, id, **kwargs):
        cache = OrganizationCache(info.context)
        return cache[id]


schema = graphene.Schema(query=Query, mutation=Mutation)

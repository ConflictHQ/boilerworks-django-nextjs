import logging

import graphene
from core.schema import UserType
from core.schema.mutations.common import UtilityForm, UtilityMutations
from core.schema.mutations.user import UserInput
from django.forms import ModelForm
from graphene_django.forms.mutation import DjangoModelFormMutation
from graphene_django.rest_framework.mutation import SerializerMutation
from graphene_django.types import ErrorType
from graphql_relay import to_global_id
from organization.models import Organization, OrganizationMember
from organization.serializers import organization_member

from ..organization import OrganizationType

logger = logging.getLogger(__name__)


class OrganizationForm(UtilityForm, ModelForm):
    class Meta:
        model = Organization
        fields = 'website', 'created_by'


class OrganizationMutation(UtilityMutations, DjangoModelFormMutation):
    organization = graphene.Field(OrganizationType)

    class Meta:
        form_class = OrganizationForm
        exclude_fields = 'created_by'

    def resolve_organization(self, info, **kwargs):
        self.check_errors()
        return self.organization


class OrganizationInput(graphene.InputObjectType):
    id = graphene.ID(required=False)
    website = graphene.String(required=False)
    organization_user = UserInput(required=False)


UtilityForm.register_form(OrganizationInput, OrganizationForm)


class UpsertOrganizationMutation(graphene.Mutation):
    # The class attributes define the response of the mutations
    organization = graphene.Field(OrganizationType)

    class Arguments:
        input_data = OrganizationInput(required=True, name="input")

    @classmethod
    def mutate(cls, root, info, input_data):
        organization = UtilityForm.apply_forms(root, info, input_data)
        return cls(organization=organization)


class OrganizationMemberStatusMutation(SerializerMutation):
    ok = graphene.Boolean()
    errors = graphene.List(ErrorType)

    class Meta:
        serializer_class = organization_member.OrganizationMemberSerializer
        lookup_field = 'id'
        fields = "__all__"

    @classmethod
    def get_serializer_kwargs(cls, root, info, **input):
        user_pk = UserType.get_pk(input['user_id'], raise_invalid_id=True)
        instance = OrganizationMember.objects.filter(member_id=user_pk,
                                                     organization_id=input['organization_id']).first()
        if instance is None:
            global_id = to_global_id(OrganizationType.__name__, input['organization_id'])
            raise ValueError(f'{input["user_id"]} is not a member of organization {global_id}')
        else:
            input['updated_by_id'] = info.context.user.id
            input['user_id'] = user_pk
            return {'instance': instance, 'data': input, 'partial': True}

    @classmethod
    def mutate_and_get_payload(cls, root, info, **input):
        if 'organization_id' not in input:
            input['organization_id'] = info.context.user.profile.organization().id
        kwargs = cls.get_serializer_kwargs(root, info, **input)
        serializer = cls._meta.serializer_class(**kwargs)

        if serializer.is_valid():
            cls.perform_mutate(serializer, info)
            return OrganizationMemberStatusMutation(ok=True, errors=())
        else:
            errors = ErrorType.from_errors(serializer.errors)
            return OrganizationMemberStatusMutation(errors=errors, ok=False)

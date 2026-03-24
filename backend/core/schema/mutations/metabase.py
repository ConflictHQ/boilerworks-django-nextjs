import graphene
from core.schema.mutations.restricted_serializer_mutation import RestrictedSerializerMutation
from core.serializers.metabase import MetabaseChartSerializer
from graphene_django.types import ErrorType


class MetabaseChartMutation(RestrictedSerializerMutation):
    ok = graphene.Boolean()
    errors = graphene.List(ErrorType)

    class Meta:
        serializer_class = MetabaseChartSerializer
        lookup_field = 'id'
        fields = "__all__"

    @classmethod
    def response(cls, ok, errors):
        return MetabaseChartMutation(ok=ok, errors=errors)

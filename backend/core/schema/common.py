import django_filters.filters
import graphene
from core.models import GlobalIDLink, Link
from django.conf import settings
from django.db.models import QuerySet
from django_filters.constants import EMPTY_VALUES
from graphene import ID, BaseGlobalIDType
from graphene.types.resolver import dict_resolver
from graphene_django import DjangoObjectType
from graphene_django.filter import GlobalIDFilter
from graphene_django.registry import get_global_registry
from graphql import GraphQLError
from graphql_relay import from_global_id, to_global_id


class CaseInsensitiveOrderingFilter(django_filters.OrderingFilter):

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        for param in value:
            from django.db.models.functions import Lower
            if param.startswith('-'):
                qs = qs.order_by(Lower(param[1:])).reverse()
            else:
                qs = qs.order_by(Lower(param))
        return qs


class GlobalIDFilterSet(django_filters.FilterSet):
    id = GlobalIDFilter(method='_filter_by_id')

    def _filter_by_id(self, queryset, name, value):
        if value is not None:
            _, _id = from_global_id(value)
            if _id is not None:
                return queryset.filter(id=_id)
        return queryset


class CustomConnection(graphene.relay.Connection):
    """
    `link total_count <https://github.com/graphql-python/graphene/issues/307>` _
    """

    class Meta:
        abstract = True

    total_count = graphene.Int()

    @staticmethod
    def resolve_total_count(root, info):
        return root.length


class SlugGlobalIDType(BaseGlobalIDType):
    graphene_type = ID

    @classmethod
    def resolve_global_id(cls, info, global_id):
        _type = info.return_type.graphene_type._meta.name
        return _type, global_id

    @classmethod
    def to_global_id(cls, _type, _id):
        return _id


class MetaNode:
    interfaces = graphene.relay.Node,
    connection_class = CustomConnection


class DjangoPermissionFilterMixin:

    @classmethod
    def get_queryset(cls, queryset: QuerySet, info) -> QuerySet:
        return queryset.model.get_queryset(queryset, info.context.user)


class DjangoObjectTypeUtils:

    def get_model(self):
        return self.graphene_type._meta.model

    @classmethod
    def to_global_id(cls, record):
        try:
            return to_global_id(str(cls), record.pk)
        except Exception as e:
            return str(e)

    @classmethod
    def get_model_pk(cls, model, global_id: graphene.ID(), raise_invalid_id: bool = True):
        registry = get_global_registry()
        return registry.get_type_for_model(model).get_pk(global_id, raise_invalid_id)

    @classmethod
    def get_pk(cls, global_id: graphene.ID(), raise_invalid_id: bool = True, check_model_name=True):
        model_name, pk = from_global_id(global_id)
        if check_model_name and not str(cls) == model_name:
            if raise_invalid_id:
                if model_name == '':
                    model_name = 'Invalid Format'
                raise GraphQLError(f'Invalid GlobalID expected {str(cls)} received {model_name} with global_id: {global_id}')
            else:
                return None
        return pk

    @classmethod
    def get_object(cls, info, global_id: graphene.ID(), raise_invalid_id: bool = True, raise_not_found=False):
        # TODO replace this with Node.get_node_from_global_id
        if not global_id and not raise_not_found:
            return None

        pk = global_id
        if isinstance(pk, str) and not global_id.isdigit():
            pk = cls.get_pk(global_id, raise_invalid_id)

        obj = cls.get_node(info, pk)

        if raise_not_found and not obj:
            if settings.DEBUG:
                raise GraphQLError(f'Object id {str(cls)}:{global_id} with pk: {pk} not found. '
                                   f'This can be related to permissions problem or wrong organization')
            raise GraphQLError(f'Object id {str(cls)}:{global_id} not found')

        return obj

    @classmethod
    def find_object(cls, global_id, app_label=None, raise_not_found=False):
        """
        Finds an object by its global id.
        """
        model_name_type, pk = from_global_id(global_id)
        model = cls.get_model_from_type(model_name_type, raise_not_found=True)
        instance = model.objects.filter(pk=pk).first()

        if not instance and raise_not_found:
            raise GraphQLError(f'Object {global_id} -> {model}:{pk} not found')

        return instance

    @classmethod
    def get_instance_from_id(cls, info, id, raise_not_found=False):
        type_name, pk = from_global_id(id)
        model = cls.get_model_from_type(type_name, raise_not_found)
        instance = model.objects.filter(pk=pk).first()
        if not instance and raise_not_found:
            raise GraphQLError('Record not found')
        return instance

    @classmethod
    def get_model_from_type(cls, type_name, raise_not_found=False):
        from graphene_django.registry import get_global_registry
        registry = get_global_registry()
        for model, value in registry._registry.items():
            if str(value) == type_name:
                return model

        if raise_not_found:
            raise GraphQLError('Model not found')
        return None


class CounterType(graphene.ObjectType, default_resolver=dict_resolver):
    id = graphene.String()
    name = graphene.String()
    count = graphene.Int()


class GlobalIDLinkType(DjangoObjectType, DjangoObjectTypeUtils):

    type_name = graphene.String()

    class Meta(MetaNode):
        model = GlobalIDLink


class LinkType(DjangoObjectType, DjangoObjectTypeUtils):

    class Meta(MetaNode):
        model = Link
        fields = 'id', 'title', 'url', 'description', 'created_at', 'updated_at'


class MoneyType(graphene.ObjectType):
    currency = graphene.String()
    amount = graphene.String()

    @staticmethod
    def resolve_amount(parent, info):
        return str(parent.amount)

    @staticmethod
    def resolve_currency(parent, info):
        return parent.currency

import django_filters
import graphene
from core.models.process import DataProcess, DataProcessEntity
from core.schema import DjangoObjectTypeUtils, DjangoPermissionFilterMixin, MetaNode
from django_filters import CharFilter
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter


class DataProcessEntityType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    class Meta(MetaNode):
        model = DataProcessEntity
        fields = ('error_message', 'line_number', 'process', 'status', 'status_date')
        filter_fields = ('process', 'status')

    process = graphene.ID(description='ID of the import process.')


class DataProcessFilter(django_filters.FilterSet):
    gid = GlobalIDFilter(method='_filter_by_gid')
    status = CharFilter(method='_filter_by_status')

    class Meta:
        model = DataProcess
        fields = ['gid', 'status']

    def _filter_by_gid(self, queryset, name, value):
        if value:
            return queryset.filter(gid=DataProcessType.get_pk(value))
        return queryset

    def _filter_by_status(self, queryset, name, value):
        if value:
            return queryset.filter(status=value)
        return queryset


class DataProcessType(DjangoPermissionFilterMixin, DjangoObjectTypeUtils, DjangoObjectType):
    class Meta(MetaNode):
        model = DataProcess
        fields = '__all__'
        filterset_class = DataProcessFilter

    gid = graphene.ID(description='Global id of the import process.')

    file_type = graphene.String(description='Extension of the uploaded file. I.E. tsv, csv, json')

    rows = graphene.List(DataProcessEntityType, description='List of rows processed from the file.')

    @staticmethod
    def resolve_rows(root: DataProcess, info, **kwargs):
        return DataProcessEntity.objects.filter(process=root)


class ProcessQuery(graphene.ObjectType):
    data_process = DjangoFilterConnectionField(
        DataProcessType,
        description="List of document importing processes, can be filtered by status and global id.")

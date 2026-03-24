from collections import defaultdict

import django_filters
import graphene
from core.dataloaders import DataLoaderContext, dataloader
from core.models import SharedDirectory, SharedFile
from core.schema import CaseInsensitiveOrderingFilter, DjangoObjectTypeUtils, MetaNode
from core.schema.upload import UploadFilter, UploadType
from django.db.models.aggregates import Count
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter


class SharedDirectoryFilter(django_filters.FilterSet):
    by_path = django_filters.CharFilter(method='_filter_by_path')

    by_path_startswith = django_filters.CharFilter(
        field_name='path',
        lookup_expr='startswith'
    )

    by_name_contains = django_filters.CharFilter(
        field_name='name',
        lookup_expr='icontains'
    )

    by_name = django_filters.CharFilter(
        field_name='name',
        lookup_expr='exact'
    )

    by_parent = GlobalIDFilter(method='_filter_by_parent')

    by_parent_path = django_filters.CharFilter(
        field_name='path',
        method='_filter_by_parent_path'
    )

    order_by = CaseInsensitiveOrderingFilter(
        fields=(
            ('display_name', 'display_name'),
        )
    )

    class Meta:
        model = SharedDirectory
        fields = [
            "by_path",
            "by_path_startswith",
            "by_name",
            "by_name_contains",
        ]

    def __init__(self, *args, **kwargs):
        if 'data' in kwargs and ('order_by' not in kwargs['data'] or kwargs['data']['order_by'] is None):
            kwargs['data']['order_by'] = 'display_name'
        super(SharedDirectoryFilter, self).__init__(*args, **kwargs)

    def filter_queryset(self, queryset):
        queryset = django_filters.FilterSet.filter_queryset(self, queryset)
        match self.data.get('by_path'):
            case '/icons':
                return queryset
            case _:
                return queryset.filter(hidden=False)

    def _filter_by_path(self, queryset, name, value):
        return queryset.filter(path=value)

    def _filter_by_parent(self, queryset, name, value):
        pk = SharedDirectoryType.get_pk(value, raise_invalid_id=True)
        return queryset.filter(parent_id=pk)

    def _filter_by_parent_path(self, queryset, name, value):
        return queryset.filter(parent__path=value)


class SharedFileFilter(django_filters.FilterSet):
    by_path = django_filters.CharFilter(
        field_name='path',
        lookup_expr='exact'
    )

    by_path_startswith = django_filters.CharFilter(
        field_name='path',
        lookup_expr='startswith'
    )

    by_parent = GlobalIDFilter(method='_filter_by_parent')

    by_parent_path = django_filters.CharFilter(
        field_name='path',
        method='_filter_by_parent_path'
    )

    by_name_contains = django_filters.CharFilter(
        field_name='file__name',
        lookup_expr='icontains'
    )

    by_name = django_filters.CharFilter(
        field_name='file__name',
        lookup_expr='exact'
    )

    order_by = CaseInsensitiveOrderingFilter(
        fields=dict(
            path='path',
        )
    )

    class Meta:
        model = SharedFile
        fields = [
            "by_path",
            "by_path_startswith",
            "by_name",
            "by_name_contains",
        ]

    def __init__(self, *args, **kwargs):
        # ToDo: bmiranda
        # if 'data' in kwargs and ('order_by' not in kwargs['data'] or kwargs['data']['order_by'] is None):
        #     kwargs['data']['order_by'] = 'display_name'
        super(SharedFileFilter, self).__init__(*args, **kwargs)

    def _filter_by_parent(self, queryset, name, value):
        pk = SharedDirectoryType.get_pk(value, raise_invalid_id=True)
        return queryset.filter(parent_id=pk)

    def _filter_by_parent_path(self, queryset, name, value):
        return queryset.filter(parent__path=value)


class SharedDirectoryType(DjangoObjectType, DjangoObjectTypeUtils):
    files = DjangoFilterConnectionField(type_=UploadType, filterset_class=UploadFilter)

    class Meta(MetaNode):
        model = SharedDirectory
        fields = '__all__'
        filterset_class = SharedDirectoryFilter

    file_count = graphene.Int()
    directory_count = graphene.Int()

    @dataloader
    @staticmethod
    def load_file_count_by_id(context: DataLoaderContext, ids: list[int], **kwargs):
        queryset = (
            SharedFile.objects
            .filter(parent__id__in=ids)
            .values('parent_id')
            .annotate(count=Count('parent_id'))
        )
        result = defaultdict(lambda: 0)
        for row in queryset:
            result[row['parent_id']] = row['count']
        for parent_id in ids:
            yield parent_id, result[parent_id]

    @dataloader
    @staticmethod
    def load_directory_count_by_id(context: DataLoaderContext, ids: list[int], **kwargs):
        queryset = (
            SharedDirectory.objects
            .filter(parent__id__in=ids)
            .values('parent_id')
            .annotate(count=Count('parent_id'))
        )
        result = defaultdict(lambda: 0)
        for row in queryset:
            result[row['parent_id']] = row['count']
        for parent_id in ids:
            yield parent_id, result[parent_id]

    @staticmethod
    def resolve_file_count(parent: SharedDirectory, info):
        return info.context.load_file_count_by_id.load(parent.id)

    @staticmethod
    def resolve_directory_count(parent: SharedDirectory, info):
        return info.context.load_directory_count_by_id.load(parent.id)


class SharedFileType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = SharedFile
        fields = '__all__'
        filterset_class = SharedFileFilter


class LibraryQuery(graphene.ObjectType):

    library = DjangoFilterConnectionField(
        SharedDirectoryType,
        description="Library, a collection of shared directories"
    )

    library_files = DjangoFilterConnectionField(
        SharedFileType,
        description="Library, a collection of shared files"
    )

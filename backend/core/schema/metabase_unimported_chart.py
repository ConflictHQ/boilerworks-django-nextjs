from datetime import timedelta

import django_filters
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from ..models import MetabaseUnimportedChart
from .common import DjangoObjectTypeUtils, MetaNode


class MetabaseUnimportedChartFilter(django_filters.FilterSet):

    class Meta:
        model = MetabaseUnimportedChart

        fields = {
            'type': ['exact'],
            'metabase_chart_id': ['exact'],
            'title': ['icontains'],
            'description': ['icontains'],
            'is_chart_imported': ['exact'],
        }


class MetabaseUnimportedChartType(DjangoObjectType, DjangoObjectTypeUtils):
    timeout = timedelta(hours=2)
    cache = caches[DEFAULT_CACHE_ALIAS]
    key = f"{MetabaseUnimportedChart.__name__}_{id(timeout)}"

    class Meta(MetaNode):
        model = MetabaseUnimportedChart
        fields = '__all__'
        filterset_class = MetabaseUnimportedChartFilter

    @classmethod
    def get_queryset(cls, queryset, info):
        result = cls.cache.get(cls.key)
        if result is None:
            result = MetabaseUnimportedChart.retrieve_and_save_unimported_metabase_charts()
            cls.cache.set(cls.key, result, cls.timeout.seconds)
        return queryset


class MetabaseUnimportedChartQuery(object):
    metabase_unimported_charts = DjangoFilterConnectionField(MetabaseUnimportedChartType, description=MetabaseUnimportedChart.__doc__)


__all__ = [
    'MetabaseUnimportedChartType',
    'MetabaseUnimportedChartQuery',
]

import django_filters
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField, GlobalIDFilter

from ..models import MetabaseChart
from .common import DjangoObjectTypeUtils, MetaNode


class MetabaseChartFilter(django_filters.FilterSet):
    id = GlobalIDFilter(method='_filter_by_id')

    class Meta:
        model = MetabaseChart

        fields = {
            'type': ['exact'],
            'metabase_chart_id': ['exact'],
            'title': ['icontains'],
            'description': ['icontains'],
        }

    def _filter_by_id(self, queryset, name, value):
        if value:
            pk = MetabaseChartType.get_pk(value, raise_invalid_id=True)
            return queryset.filter(pk=pk)
        return queryset


class MetabaseChartType(DjangoObjectType, DjangoObjectTypeUtils):
    iframe_url = graphene.String()

    class Meta(MetaNode):
        model = MetabaseChart
        fields = '__all__'
        filterset_class = MetabaseChartFilter


class MetabaseChartQuery(object):
    metabase_charts = DjangoFilterConnectionField(MetabaseChartType, description=MetabaseChart.__doc__)


__all__ = [
    'MetabaseChartType',
    'MetabaseChartQuery',
]

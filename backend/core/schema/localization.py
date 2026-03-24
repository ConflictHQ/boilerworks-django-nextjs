import django_filters
import graphene
from config import settings
from django_filters import CharFilter, ChoiceFilter
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField

from ..models.internationalization import SiteLabel
from .common import DjangoObjectTypeUtils, MetaNode


class SiteLabelFilter(django_filters.FilterSet):
    key = CharFilter(method='_filter_by_key')
    locale = ChoiceFilter(method='_filter_by_locale', choices=settings.LANGUAGES)

    class Meta:
        model = SiteLabel
        fields = ['key', 'locale']

    def __init__(self, *args, **kwargs):
        if kwargs['data'].get('locale', None) is None:
            kwargs['data']['locale'] = settings.LANGUAGE_CODE
        super(SiteLabelFilter, self).__init__(*args, **kwargs)

    def _filter_by_key(self, queryset, name, value):
        if value:
            return queryset.filter(key__startswith=value)
        return queryset

    def _filter_by_locale(self, queryset, name, value=settings.LANGUAGE_CODE):

        return queryset.filter(locale__language_code=value)


class SiteLabelType(DjangoObjectType, DjangoObjectTypeUtils):
    class Meta(MetaNode):
        model = SiteLabel
        fields = '__all__'
        filterset_class = SiteLabelFilter


class SiteLabelQuery(graphene.ObjectType):
    site_labels = DjangoFilterConnectionField(
        SiteLabelType,
        description="List of text labels to display on site, can be filtered by language and key.")

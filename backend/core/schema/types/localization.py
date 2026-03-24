from __future__ import annotations

import django_filters
import strawberry
import strawberry_django
from config import settings
from django_filters import CharFilter, ChoiceFilter
from strawberry.types import Info

from core.models.internationalization import SiteLabel


class SiteLabelFilter(django_filters.FilterSet):
    key = CharFilter(method='_filter_by_key')
    locale = ChoiceFilter(method='_filter_by_locale', choices=settings.LANGUAGES)

    class Meta:
        model = SiteLabel
        fields = ['key', 'locale']

    def __init__(self, *args, **kwargs):
        if kwargs['data'].get('locale', None) is None:
            kwargs['data']['locale'] = settings.LANGUAGE_CODE
        super().__init__(*args, **kwargs)

    def _filter_by_key(self, queryset, name, value):
        if value:
            return queryset.filter(key__startswith=value)
        return queryset

    def _filter_by_locale(self, queryset, name, value=settings.LANGUAGE_CODE):
        return queryset.filter(locale__language_code=value)


@strawberry_django.type(SiteLabel)
class SiteLabelType:
    pass

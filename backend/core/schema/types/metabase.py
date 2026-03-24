from __future__ import annotations

from datetime import timedelta
from typing import Optional

import strawberry
import strawberry_django
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from strawberry.types import Info

from core.models import MetabaseChart, MetabaseUnimportedChart


@strawberry_django.type(MetabaseChart)
class MetabaseChartType:
    iframe_url: Optional[str]


@strawberry_django.type(MetabaseUnimportedChart)
class MetabaseUnimportedChartType:
    _timeout = timedelta(hours=2)
    _cache = caches[DEFAULT_CACHE_ALIAS]
    _cache_key = f"{MetabaseUnimportedChart.__name__}_cache"

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        result = cls._cache.get(cls._cache_key)
        if result is None:
            result = MetabaseUnimportedChart.retrieve_and_save_unimported_metabase_charts()
            cls._cache.set(cls._cache_key, result, cls._timeout.seconds)
        return queryset

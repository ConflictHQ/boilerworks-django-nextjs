from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from core.models.process import DataProcess, DataProcessEntity
from core.strawberry_schema.common import permission_filtered_queryset


@strawberry_django.type(DataProcessEntity)
class DataProcessEntityType:
    error_message: Optional[str]
    line_number: Optional[int]
    status: Optional[str]
    status_date: Optional[str]
    process: strawberry.ID

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)


@strawberry_django.type(DataProcess)
class DataProcessType:
    gid: strawberry.ID
    file_type: Optional[str]

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)

    @strawberry_django.field
    def rows(self, info: Info) -> list[DataProcessEntityType]:
        return DataProcessEntity.objects.filter(process=self)

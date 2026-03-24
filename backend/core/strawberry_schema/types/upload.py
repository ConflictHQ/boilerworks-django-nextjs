from __future__ import annotations

from typing import Optional

import strawberry
import strawberry_django
from strawberry.types import Info

from core.models import Upload
from core.models.upload import FileUpload
from core.strawberry_schema.common import permission_filtered_queryset


@strawberry_django.type(Upload)
class UploadType:
    name: Optional[str]
    description: Optional[str]
    content_type: Optional[str]
    metadata: Optional[strawberry.scalars.JSON]
    location: Optional[str]
    target_global_id: str

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return queryset.with_view_permission_info(info).filter(deleted_at__isnull=True)

    @strawberry_django.field(deprecation_reason="Use file_url instead.")
    def public_transient_url(self, info: Info) -> Optional[str]:
        organization = info.context.user.profile.organization()
        path = Upload.generate_path(
            location=Upload.Location(self.location),
            organization=organization,
            target_global_id=self.target_global_id,
            uuid=self.id,
            mimetype=self.content_type,
        )
        return Upload.generate_pre_signed_url_for_get(name=path)

    @strawberry_django.field
    def pre_signed_url(self, info: Info) -> Optional[str]:
        organization = info.context.user.profile.organization()
        path = Upload.generate_path(
            location=Upload.Location(self.location),
            organization=organization,
            target_global_id=self.target_global_id,
            uuid=self.id,
            mimetype=self.content_type,
        )
        return Upload.generate_pre_signed_url_for_put(
            name=path,
            content_type=self.content_type,
        )

    @strawberry_django.field
    def file_url(self, info: Info) -> Optional[str]:
        user = info.context.user
        if user.is_authenticated:
            organization = user.profile.organization()
            path = Upload.generate_path(
                location=Upload.Location(self.location),
                organization=organization,
                target_global_id=self.target_global_id,
                uuid=self.id,
                mimetype=self.content_type,
            )
            return Upload.generate_pre_signed_url_for_get(name=path)
        return None

    @strawberry_django.field(deprecation_reason="Use file_url instead.")
    def public_permanent_url(self, info: Info) -> Optional[str]:
        if Upload.Location(self.location) == Upload.Location.PUBLIC:
            return self.public_url.split('?')[0]
        return None


@strawberry_django.type(FileUpload)
class FileUploadType:
    path: Optional[str]
    content_type: Optional[str]
    public_url: Optional[str]
    pre_signed_url: Optional[str]
    target_global_id: str

    @classmethod
    def get_queryset(cls, queryset, info: Info):
        return permission_filtered_queryset(queryset, info)

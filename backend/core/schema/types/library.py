from __future__ import annotations

from typing import Optional

import strawberry_django
from strawberry.types import Info

from core.models import SharedDirectory, SharedFile
from core.schema.dataloaders import batch_load_directory_counts, batch_load_file_counts


@strawberry_django.type(SharedDirectory)
class SharedDirectoryType:

    @strawberry_django.field
    async def file_count(self, info: Info) -> int:
        loader = info.context.get_loader('load_file_count_by_id', batch_load_file_counts)
        return await loader.load(self.id)

    @strawberry_django.field
    async def directory_count(self, info: Info) -> int:
        loader = info.context.get_loader('load_directory_count_by_id', batch_load_directory_counts)
        return await loader.load(self.id)


@strawberry_django.type(SharedFile)
class SharedFileType:
    pass

"""Library mutations migrated from Graphene to Strawberry."""
from __future__ import annotations

from typing import Optional

import strawberry
from graphql import GraphQLError
from strawberry.types import Info

from core.models import SharedDirectory, SharedFile, Upload
from core.schema.types.library import SharedDirectoryType as StrawberrySharedDirectoryType
from core.schema.types.upload import UploadType as StrawberryUploadType


# ---------------------------------------------------------------------------
# Helpers — resolve objects using the Graphene registry (same as originals)
# ---------------------------------------------------------------------------

def _get_shared_directory(info, global_id: str, raise_not_found: bool = True) -> SharedDirectory:
    from core.schema.library import SharedDirectoryType
    return SharedDirectoryType.get_object(info, global_id, raise_not_found=raise_not_found)


def _get_upload(info, global_id: str, raise_not_found: bool = True) -> Upload:
    from core.schema.upload import UploadType
    return UploadType.get_object(info, global_id, raise_not_found=raise_not_found)


# ---------------------------------------------------------------------------
# Response types
# ---------------------------------------------------------------------------

@strawberry.type
class LibraryMkdirResult:
    ok: bool
    directory: Optional[StrawberrySharedDirectoryType]


@strawberry.type
class LibraryRenameDirectoryResult:
    ok: bool
    directory: Optional[StrawberrySharedDirectoryType]


@strawberry.type
class LibraryRenameFileResult:
    ok: bool
    file: Optional[StrawberryUploadType]


@strawberry.type
class LibraryRmFileResult:
    ok: bool
    directory: Optional[StrawberrySharedDirectoryType]


@strawberry.type
class LibrarySetIconResult:
    ok: bool
    directory: Optional[StrawberrySharedDirectoryType]


# ---------------------------------------------------------------------------
# Mutations
# ---------------------------------------------------------------------------

@strawberry.type
class LibraryMutations:

    @strawberry.mutation(description="Create a new directory in the library.")
    def library_mkdir(
        self,
        info: Info,
        name: str,
        parent_guid: Optional[strawberry.ID] = None,
        icon: Optional[strawberry.ID] = None,
    ) -> LibraryMkdirResult:
        parent: Optional[SharedDirectory] = None
        match parent_guid:
            case str() | int():
                parent = _get_shared_directory(info, parent_guid, raise_not_found=True)
            case None:
                parent = None

        directory = SharedDirectory.objects.mkdir(
            path=parent, name=name, created_by=info.context.user,
        )

        if icon is not None:
            upload = _get_upload(info, icon, raise_not_found=True)
            directory.icon = upload
            directory.save()

        return LibraryMkdirResult(ok=True, directory=directory)

    @strawberry.mutation(description="Remove a directory from the library.")
    def library_rmdir(self, info: Info, directory_guid: strawberry.ID) -> bool:
        directory: Optional[SharedDirectory] = None
        match directory_guid:
            case str() | int():
                directory = _get_shared_directory(info, directory_guid, raise_not_found=True)
            case _:
                return False

        directory.delete()
        return True

    @strawberry.mutation(description="Rename a directory in the library.")
    def library_rename_dir(
        self,
        info: Info,
        name: str,
        guid: strawberry.ID,
    ) -> LibraryRenameDirectoryResult:
        directory = _get_shared_directory(info, guid, raise_not_found=True)
        directory = SharedDirectory.objects.rename(directory=directory, name=name)
        return LibraryRenameDirectoryResult(ok=True, directory=directory)

    @strawberry.mutation(description="Rename a file in the library.")
    def library_rename_file(
        self,
        info: Info,
        name: str,
        guid: strawberry.ID,
    ) -> LibraryRenameFileResult:
        upload = _get_upload(info, guid, raise_not_found=True)
        upload.name = name
        upload.save()
        queryset = list(SharedFile.objects.filter(file=upload))
        for shared_file in queryset:
            SharedFile.objects.rename(shared_file=shared_file, name=name)
        return LibraryRenameFileResult(ok=True, file=upload)

    @strawberry.mutation(description="Remove a file from a library directory.")
    def library_rm_file(
        self,
        info: Info,
        directory: strawberry.ID,
        file: strawberry.ID,
    ) -> LibraryRmFileResult:
        upload: Upload = _get_upload(info, file, raise_not_found=True)
        dir_obj: SharedDirectory = _get_shared_directory(info, directory, raise_not_found=True)

        queryset = SharedFile.objects.filter(
            file=upload,
            parent=dir_obj,
        )

        if queryset.exists():
            queryset.delete()
            return LibraryRmFileResult(ok=True, directory=dir_obj)

        return LibraryRmFileResult(ok=False, directory=dir_obj)

    @strawberry.mutation(description="Set the icon for a library directory.")
    def library_set_icon(
        self,
        info: Info,
        directory: strawberry.ID,
        file: strawberry.ID,
    ) -> LibrarySetIconResult:
        upload: Upload = _get_upload(info, file, raise_not_found=True)
        dir_obj: SharedDirectory = _get_shared_directory(info, directory, raise_not_found=True)

        dir_obj.icon = upload
        dir_obj.save()

        icons = SharedDirectory.objects.get_by_path('/icons')
        if icons is not None:
            if not icons.files.contains(upload):
                icons.files.add(upload)
                icons.save()

        return LibrarySetIconResult(ok=False, directory=dir_obj)

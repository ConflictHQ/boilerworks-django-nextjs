from typing import Optional

import graphene
from core.models import SharedDirectory, SharedFile, Upload
from core.schema.library import SharedDirectoryType
from core.schema.upload import UploadType


class LibraryMkdirMutation(graphene.Mutation):
    ok = graphene.Boolean()

    directory = graphene.Field(SharedDirectoryType)

    class Arguments:
        name = graphene.String(description='name of the directory', required=True)
        parent_guid = graphene.ID(description='Parent Directory Global Id', required=False)
        icon = graphene.ID(description='File Global Id of the Icon', required=False)

    @classmethod
    def mutate(
            cls,
            root,
            info,
            name: str,
            parent_guid: Optional[str] = None,
            icon: Optional[str | int] = None
    ):
        parent: Optional[SharedDirectory]
        match parent_guid:
            case str() | int():
                parent: SharedDirectory = SharedDirectoryType.get_object(
                    info,
                    parent_guid,
                    raise_not_found=True
                )
            case None:
                parent = None

        directory = SharedDirectory.objects.mkdir(path=parent, name=name, created_by=info.context.user)

        if icon is not None:
            upload = UploadType.get_object(
                info,
                icon,
                raise_not_found=True
            )
            directory.icon = upload
            directory.save()

        return cls(ok=True, directory=directory)


class LibraryRmdirMutation(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        directory_guid = graphene.ID(description='Parent Directory Global Id', required=True)

    @classmethod
    def mutate(cls, root, info, directory_guid: str = None):

        directory: Optional[SharedDirectory]
        match directory_guid:
            case str() | int():
                directory: SharedDirectory = SharedDirectoryType.get_object(
                    info,
                    directory_guid,
                    raise_not_found=True
                )
            case _:
                return cls(ok=False)

        directory.delete()

        return cls(ok=True)


class LibraryRenameDirectoryMutation(graphene.Mutation):
    ok = graphene.Boolean()

    directory = graphene.Field(SharedDirectoryType)

    class Arguments:
        name = graphene.String(description='New name of the directory', required=True)
        guid = graphene.ID(description='Directory Global Id', required=True)

    @classmethod
    def mutate(cls, root, info, name: str, guid: Optional[str] = None):
        directory: SharedDirectory = SharedDirectoryType.get_object(info, guid, raise_not_found=True)
        directory = SharedDirectory.objects.rename(directory=directory, name=name)
        return cls(ok=True, directory=directory)


class LibraryRenameFileMutation(graphene.Mutation):

    ok = graphene.Boolean()

    file = graphene.Field(UploadType)

    class Arguments:
        name = graphene.String(description='New name of the directory', required=True)
        guid = graphene.ID(description='Directory Global Id', required=True)

    @classmethod
    def mutate(cls, root, info, name: str, guid: Optional[str] = None):
        upload: UploadType = UploadType.get_object(info, guid, raise_not_found=True)
        upload.name = name
        upload.save()
        queryset = list(SharedFile.objects.filter(file=upload))
        for shared_file in queryset:
            SharedFile.objects.rename(shared_file=shared_file, name=name)
        return cls(ok=True, file=upload)


class LibraryRmFileMutation(graphene.Mutation):

    ok = graphene.Boolean()

    directory = graphene.Field(SharedDirectoryType)

    class Arguments:
        directory = graphene.ID(description='Directory Global Id', required=True)
        file = graphene.ID(description='File Global Id', required=True)

    @classmethod
    def mutate(cls, root, info, directory: str | int, file: str | int):
        upload: Upload = UploadType.get_object(info, file, raise_not_found=True)
        directory: SharedDirectory = SharedDirectoryType.get_object(info, directory, raise_not_found=True)

        queryset = SharedFile.objects.filter(
            file=upload,
            parent=directory,
        )

        if queryset.exists():
            queryset.delete()
            return cls(ok=True, directory=directory)

        return cls(ok=False, directory=directory)


class LibrarySetIconMutation(graphene.Mutation):

    ok = graphene.Boolean()

    directory = graphene.Field(SharedDirectoryType)

    class Arguments:
        directory = graphene.ID(description='Directory Global Id', required=True)
        file = graphene.ID(description='File Global Id', required=True)

    @classmethod
    def mutate(cls, root, info, directory: str | int, file: str | int):
        upload: Upload = UploadType.get_object(info, file, raise_not_found=True)
        directory: SharedDirectory = SharedDirectoryType.get_object(info, directory, raise_not_found=True)

        directory.icon = upload
        directory.save()

        icons = SharedDirectory.objects.get_by_path('/icons')
        if icons is not None:
            if not icons.files.contains(upload):
                icons.files.add(upload)
                icons.save()

        return cls(ok=False, directory=directory)

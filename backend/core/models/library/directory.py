import contextlib
import os
from typing import Any, Optional

import pydash
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.related import RECURSIVE_RELATIONSHIP_CONSTANT

from ..authorization.principal import SharedResource
from ..common import Tracking
from ..upload import Upload


class SharedFileManager(models.Manager):
    use_in_migrations = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache shared by all the get_for_* methods to speed up
        # ContentType retrieval.
        self._by_path = {}

    @classmethod
    def get_path_from_parent_and_file(cls, parent: "SharedDirectory", file: Upload):
        return os.path.join(parent.path, file.name)

    def get_by_path(self, path) -> Optional["SharedFile"]:
        result: Optional[SharedFile] = self._by_path.get(path)
        if result is not None:
            return result
        result = self.filter(path=path).first()
        if result is not None:
            self._by_path[path] = result
        return result

    def rename(
            self,
            shared_file: Optional["SharedFile"],
            name: str,
            display_name: Optional[str] = None,
    ):
        # Files today do not have display, do we need it?
        # safe_name: str = pydash.camel_case(name)
        # display_name = display_name or name
        upload = shared_file.file

        if upload.name != name:
            upload.name = name
            upload.save()
        shared_file.clean()
        shared_file.save()
        return shared_file


class SharedFile(Tracking, SharedResource):
    class Meta:
        ordering = ('path',)

    objects = SharedFileManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.objects = SharedFile.objects

    file = models.ForeignKey(
        Upload,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='+',
    )

    parent = models.ForeignKey(
        "SharedDirectory",
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='+',
    )

    path = models.CharField(max_length=1024, unique=True)

    def clean(self):
        self.path = self.objects.get_path_from_parent_and_file(self.parent, self.file)

    def __str__(self):
        return f'Shared File: {self.path}'


class SharedDirectoryManager(models.Manager):
    use_in_migrations = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache shared by all the get_for_* methods to speed up
        # ContentType retrieval.
        self._by_path = {}

    def get_queryset(self):
        return (
            super(models.Manager, self)
            .get_queryset()
            # .filter(hidden=False)
        )

    def get_by_path(self, path) -> Optional["SharedDirectory"]:
        result: Optional[SharedDirectory] = self._by_path.get(path)
        if result is not None:
            return result
        result = self.filter(path=path).first()
        if result is not None:
            self._by_path[path] = result
        return result

    def init(self):
        root: Optional['SharedDirectory'] = self.filter(path=os.path.sep).first()
        match root:
            case None:
                root = self.create(path=os.path.sep, name="")
        self.filter(parent__isnull=True).exclude(id=root.id).update(parent=root)

    def rename(
            self,
            directory: Optional["SharedDirectory"],
            name: str,
            display_name: Optional[str] = None,
    ):
        safe_name: str = pydash.camel_case(name)
        display_name = display_name or name
        directory.name = safe_name
        directory.display_name = display_name
        visitor = UpdateChildrenPathVisitor()
        visitor.visit(directory)
        return directory

    def mkdir(
            self,
            path: Optional[Any],
            name: str,
            display_name: Optional[str] = None,
            created_by: Optional[Any] = None,
            hidden: bool = False,
    ) -> "SharedDirectory":

        full_path: str
        directory: Optional["SharedDirectory"]
        parent: Optional["SharedDirectory"]
        safe_name: str = pydash.camel_case(name)

        match path:
            case None | "/":
                parent = None
                full_path = os.path.join("/", safe_name)
            case str():
                parent = self.get_by_path(path)
                if parent is None:
                    raise AssertionError(f'Parent "{path}" does not exist')
                full_path = os.path.join(path, safe_name)
            case SharedDirectory(path=parent_path):
                parent = path
                full_path = os.path.join(parent_path, safe_name)
            case _:
                raise AssertionError(f'Parent "{path}" is not supported')

        if (directory := self.get_by_path(full_path)) is not None:
            return directory

        display_name = display_name or name

        directory = self.create(
            name=safe_name,
            display_name=display_name,
            parent=parent,
            path=full_path,
            created_by=created_by,
            hidden=hidden,
        )
        return directory

    def rmdir(
            self,
            path: str,
    ) -> None:
        self.filter(path=path).delete()


class SharedDirectory(Tracking, SharedResource):
    class Meta:
        ordering = ('path',)

    objects = SharedDirectoryManager()

    name = models.CharField(max_length=128, null=False, blank=False)

    display_name = models.CharField(max_length=128, null=False, blank=False)

    path = models.CharField(max_length=1024, unique=True)

    icon = models.ForeignKey(
        Upload,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='folders',
        help_text='Image associated with the shared directory.',
    )

    owners = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
    )

    files = models.ManyToManyField(
        Upload,
        through=SharedFile,
        blank=True,
        related_name='+',
        help_text='Files'
    )

    parent = models.ForeignKey(
        RECURSIVE_RELATIONSHIP_CONSTANT,
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )

    hidden = models.BooleanField(default=False)

    @property
    def __parent__(self) -> Optional["SharedDirectory"]:
        return self.parent

    @property
    def __path__(self) -> str:
        name = self.safe_name(self.name)
        if (self_parent := self.__parent__) is None:
            return os.path.join(os.path.sep, name)
        return os.path.join(self_parent.__path__, name)

    def __str__(self):
        return f"Shared Directory: {self.path}"

    @classmethod
    def safe_name(cls, name: str) -> str:
        return pydash.camel_case(name)

    def clean(self):
        self.__assert_not_loop_created()

        # Makes sure the name is path safe
        self.name = self.safe_name(self.name)

        old_path = self.path
        new_path = self.__path__
        self._path_modified = old_path != new_path

        if self._path_modified:
            self.path = new_path

        return None

    @contextlib.contextmanager
    def _on_path_consistency_guard(self):

        if not hasattr(self, '_path_modified'):
            self.clean()

        yield

        if self._path_modified:

            for child in self.children.all():
                child.clean()
                child.save()

            for child in self.files.all():
                child.clean()
                child.save()

    def save(self, *args, **kwargs):
        with self._on_path_consistency_guard():
            super().save(*args, **kwargs)

    def __assert_not_loop_created(self):
        parents: set[int] = {self.id}
        node: SharedDirectory = self

        while (parent_node := node.__parent__) is not None:
            if parent_node.id in parents:
                message = f'Loop on nodes: {parents}'
                raise ValidationError(message)
            node = parent_node
            parents.add(parent_node.id)


class SharedDirectoryVisitor:

    def __init__(self):
        pass

    def visit(self, directory: SharedDirectory) -> None:
        if not self.accept_directory(directory):
            return

        self.on_visit_directory(directory)

        if self.accept_sub_directories(directory):
            for child in SharedDirectory.objects.filter(parent=directory):
                if self.accept_file(child):
                    self.on_visit_file(child)

        if self.accept_files(directory):
            for child in SharedFile.objects.filter(parent=directory):
                self.on_visit_file(child)

    def accept_directory(self, directory: SharedDirectory) -> bool:
        return True

    def accept_sub_directories(self, directory: SharedDirectory) -> bool:
        return True

    def accept_files(self, directory: SharedDirectory) -> bool:
        return True

    def accept_file(self, file: SharedFile) -> bool:
        return True

    def on_visit_directory(self, directory: SharedDirectory) -> None:
        pass

    def on_visit_file(self, file: SharedFile) -> None:
        pass


class UpdateChildrenPathVisitor(SharedDirectoryVisitor):

    def on_visit_directory(self, directory: SharedDirectory) -> None:
        directory.clean()
        directory.save()

    def on_visit_file(self, file: SharedFile) -> None:
        file.clean()
        file.save()


__all__ = [
    'SharedDirectory',
    'SharedDirectoryManager',
    'SharedDirectoryVisitor',
    'SharedFile',
    'SharedFileManager',
]

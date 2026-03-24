import abc
import enum
from typing import Iterable, OrderedDict

from django.core.handlers.wsgi import WSGIRequest
from django.db.models import QuerySet
from django.http import HttpResponse, QueryDict


class FileExport(abc.ABC):
    headers: OrderedDict[str, int]
    default_value: str

    @abc.abstractmethod
    def validate_params(self, request: WSGIRequest) -> None | HttpResponse:
        ...

    @abc.abstractmethod
    def get_filename(self, params: QueryDict) -> str:
        ...

    @abc.abstractmethod
    def get_queryset(self, request: WSGIRequest) -> QuerySet | HttpResponse | Iterable:
        ...

    @abc.abstractmethod
    def iter_items(self, queryset, buffer):
        ...


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """

    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


class SupportedFileFormats(enum.Enum):
    CSV = 'csv', ','
    TSV = 'tsv', '\t'
    PDF = 'pdf', None

    @classmethod
    def extensions(cls) -> list[str]:
        return [item.value[0] for item in cls]

    @classmethod
    def from_value(cls, value: str) -> 'SupportedFileFormats':
        for item in cls:
            if item.extension() == value:
                return item
        raise ValueError(f"{value!r} is not a valid {cls.__name__}")

    @classmethod
    def has_value(cls, value: str) -> bool:
        return value in (item.extension() for item in cls)

    def delimiter(self) -> str:
        return self.value[1]

    def extension(self) -> str:
        return self.value[0]

    def __str__(self):
        return self.value[0]


class FileExportMixin:

    def get_content_type(self) -> str:
        file_format = getattr(self, 'file_format', None)
        if file_format and isinstance(file_format, SupportedFileFormats):
            if file_format == SupportedFileFormats.PDF:
                return 'application/pdf'
            elif file_format == SupportedFileFormats.CSV:
                return 'text/csv'
            elif file_format == SupportedFileFormats.TSV:
                return 'text/tsv'

        return 'text/tsv'

    def _raise_pdf_not_supported(self):
        raise NotImplementedError(f"PDF format is not supported for {self.__class__.__name__}")

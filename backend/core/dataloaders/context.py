import logging
from collections import defaultdict
from typing import TYPE_CHECKING, Any, Callable, List

from django.conf import settings
from django.utils.functional import cached_property

from .sync_dataloader import DataloaderBatchCallbacks, SyncDataLoader

if TYPE_CHECKING:
    from organization.models import Organization

logger = logging.getLogger(__name__)

_registered_dataloaders = {}
_registered_dataloader_caches = {}


class DataLoaderContext:
    """
    A context value containing requested dataloaders, caches,  and callbacks.
    """

    def __init__(self, request):
        self.request = request
        self.callbacks: DataloaderBatchCallbacks = DataloaderBatchCallbacks()
        self.dataloader: dict[str, SyncDataLoader] = {}
        self.caches = {}
        self.cached_permissions: dict[str, bool] = {}

    @cached_property
    def user(self):
        """
        Returns the authenticated user
        """
        return self.request.user

    @cached_property
    def session(self):
        """
        Returns the session of the user
        """
        return self.request.session

    def run_all_callbacks(self):
        """
        Executes all pending callbacks
        """
        self.callbacks.run_all_callbacks()

    def check_permission(self, permission_name: str, callback: Callable[[], bool]) -> bool:
        if permission_name not in self.cached_permissions:
            self.cached_permissions[permission_name] = callback()
        return self.cached_permissions[permission_name]

    @cached_property
    def request_language(self) -> str:
        """
        Provides the language of the request. It follows this precedence:
        - User profile preferred language, if it was set
        - Otherwise, the Accept-Language header.
        """
        return (
                self.user.profile.preferred_language
                or self.request.headers.get('Accept-Language', settings.LANGUAGE_CODE)[:2]
        )

    @cached_property
    def organization(self) -> 'Organization':
        return self.user.profile.organization()

    def __getattr__(self, item):
        if item in self.dataloader:
            return self.dataloader[item]
        if item in _registered_dataloaders:
            self.dataloader[item] = _registered_dataloaders[item](self)
            return self.dataloader[item]
        return super().__getattribute__(item)


def dataloader(func: Callable) -> Callable[[DataloaderBatchCallbacks], SyncDataLoader]:
    """
    Register the decorated function as a dataloader callback
    """

    def new_dataloader(context: "DataLoaderContext") -> SyncDataLoader:
        """
        Creates a new dataloader with the given DataLoader Context
        """
        def batch_load_fn(keys: List[Any]) -> List[Any]:
            """
            Batch load function that returns a list of values for the given keys.
            """
            mapping = defaultdict(lambda: None)
            for key, value in func(context, keys):
                mapping[key] = value
            return [mapping[key] for key in keys]

        return SyncDataLoader(batch_load_fn, context.callbacks)

    assert func.__name__ not in _registered_dataloaders
    _registered_dataloaders[func.__name__] = new_dataloader

    return new_dataloader


def dataloader_cache(original_class):
    """
    Registers the given cache in the DataLoaderContext

    The pattern is:

    ```python
    @dataloader_cache
    class MyCache:
        def __init__(context: DataLoaderContext):
            ...
    ```

    This decorator modifies the class definition by adding a
    `__new__` method which controls the instance creation.

    It works similarly to the `@cached_property`.
    It stores the cache instance inside the context instance avoiding
    creating more than one cache by request.
    """

    def __new__(cls, context: DataLoaderContext):
        if cls not in context.caches:
            instance = object.__new__(cls)
            original_class.__init__(instance, context)
            context.caches[cls] = instance
        return context.caches[cls]

    original_class.__new__ = __new__

    return original_class

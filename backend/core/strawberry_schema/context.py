from __future__ import annotations

from typing import Any, Callable

from asgiref.sync import sync_to_async
from django.conf import settings
from django.utils.functional import cached_property
from strawberry.dataloader import DataLoader


class StrawberryContext:
    """Request context for Strawberry GraphQL resolvers.

    Replaces the Graphene DataLoaderContext. Provides:
    - Cached user/session/organization properties
    - Lazy dataloader creation via get_loader()
    - Per-request permission caching
    """

    def __init__(self, request):
        self.request = request
        self._loaders: dict[str, DataLoader] = {}
        self.cached_permissions: dict[str, bool] = {}

    @cached_property
    def user(self):
        return self.request.user

    @cached_property
    def session(self):
        return self.request.session

    @cached_property
    def organization(self):
        return self.user.profile.organization()

    @cached_property
    def request_language(self) -> str:
        """Language of the request. Prefers user profile setting, then Accept-Language header."""
        return (
            self.user.profile.preferred_language
            or self.request.headers.get('Accept-Language', settings.LANGUAGE_CODE)[:2]
        )

    def check_permission(self, permission_name: str, callback: Callable[[], bool]) -> bool:
        """Check a permission with per-request caching."""
        if permission_name not in self.cached_permissions:
            self.cached_permissions[permission_name] = callback()
        return self.cached_permissions[permission_name]

    def get_loader(self, name: str, batch_fn: Callable) -> DataLoader:
        """Get or create a DataLoader for the given batch function.

        Loaders are created lazily and cached per-request to ensure
        proper batching across a single GraphQL execution.
        """
        if name not in self._loaders:
            self._loaders[name] = DataLoader(load_fn=batch_fn)
        return self._loaders[name]

    # -----------------------------------------------------------------------
    # Convenience loader accessors (match the old info.context.loader_name pattern)
    # -----------------------------------------------------------------------

    @cached_property
    def _organization_cache(self) -> dict[int, Any]:
        """Per-request cache of all organizations, keyed by ID."""
        from organization.models import Organization
        return {org.id: org for org in Organization.objects.all()}

    def get_organization_cached(self, org_id: int):
        """Look up an organization from the per-request cache."""
        return self._organization_cache.get(org_id)

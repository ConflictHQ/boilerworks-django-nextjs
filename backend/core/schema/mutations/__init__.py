"""Core Strawberry mutations — assembled from individual modules."""
from __future__ import annotations

from typing import Optional

import strawberry
from strawberry.types import Info

from core.schema.common import MutationResult
from core.schema.mutations.base import activate_mutation, delete_mutation
from core.schema.mutations.library import LibraryMutations
from core.schema.mutations.metabase import MetabaseMutations
from core.schema.mutations.notification import NotificationMutations
from core.schema.mutations.permissions import PermissionMutations
from core.schema.mutations.rocketchat import RocketchatMutations
from core.schema.mutations.upload import UploadMutations
from core.schema.mutations.user import UserMutations


@strawberry.type
class Mutation(
    UserMutations,
    NotificationMutations,
    PermissionMutations,
    LibraryMutations,
    RocketchatMutations,
    MetabaseMutations,
    UploadMutations,
):
    """Root mutation type for the core Strawberry schema.

    Inherits mutation fields from each domain-specific mixin class.
    Also exposes the generic delete and activate mutations directly.
    """

    @strawberry.mutation(description="Delete an object by its global ID (soft-delete via delete_check).")
    def delete(self, info: Info, gid: strawberry.ID) -> bool:
        return delete_mutation(info, gid)

    @strawberry.mutation(description="Activate or deactivate an object by its global ID.")
    def activate(self, info: Info, gid: strawberry.ID, active: bool = True) -> bool:
        return activate_mutation(info, gid, active)

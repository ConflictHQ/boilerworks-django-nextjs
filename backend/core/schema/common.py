from __future__ import annotations

from typing import Generic, Optional, Sequence, TypeVar

import django_filters
import strawberry
import strawberry.relay
import strawberry_django
from django.db.models import QuerySet
from django_filters.constants import EMPTY_VALUES
from graphql import GraphQLError
from strawberry import relay
from strawberry.types import Info

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Custom relay connection with total_count
# ---------------------------------------------------------------------------

@strawberry.type(description="A connection with total count support.")
class CustomConnection(relay.ListConnection[T], Generic[T]):
    """Relay connection that includes total_count for pagination."""

    @strawberry.field(description="Total number of items in the connection.")
    def total_count(self) -> int:
        nodes = self.nodes
        if isinstance(nodes, QuerySet):
            return nodes.count()
        if hasattr(nodes, '__len__'):
            return len(nodes)
        return 0


# ---------------------------------------------------------------------------
# Validation / mutation result types
# ---------------------------------------------------------------------------

@strawberry.type(description="A field-level validation error.")
class ValidationError:
    field: str
    messages: list[str]


@strawberry.type(description="Standard mutation result with ok flag and validation errors.")
class MutationResult:
    ok: bool
    errors: list[ValidationError] = strawberry.field(default_factory=list)

    @classmethod
    def success(cls) -> MutationResult:
        return cls(ok=True, errors=[])

    @classmethod
    def from_serializer_errors(cls, errors: dict) -> MutationResult:
        """Convert DRF serializer errors dict to MutationResult."""
        flat_errors = unpack_nested_errors(errors)
        return cls(ok=False, errors=flat_errors)

    @classmethod
    def from_form_errors(cls, errors: dict) -> MutationResult:
        """Convert Django form errors dict to MutationResult."""
        flat_errors = [
            ValidationError(field=field, messages=[str(m) for m in msgs])
            for field, msgs in errors.items()
        ]
        return cls(ok=False, errors=flat_errors)


def unpack_nested_errors(errors: dict, prefix: str | None = None) -> list[ValidationError]:
    """Recursively flatten nested DRF validation errors."""
    result = []
    for key, value in errors.items():
        field = f"{prefix}.{key}" if prefix else key
        if isinstance(value, list):
            result.append(ValidationError(field=field, messages=[str(m) for m in value]))
        elif isinstance(value, dict):
            result.extend(unpack_nested_errors(value, prefix=field))
    return result


# ---------------------------------------------------------------------------
# Global ID utilities
# ---------------------------------------------------------------------------

class GlobalIDUtils:
    """Utility methods for working with relay Global IDs in Strawberry."""

    @staticmethod
    def to_global_id(type_name: str, pk) -> str:
        """Encode a type name and PK into a relay global ID."""
        return relay.to_base64(type_name, pk)

    @staticmethod
    def from_global_id(global_id: str) -> tuple[str, str]:
        """Decode a relay global ID into (type_name, pk)."""
        type_name, node_id = relay.from_base64(global_id)
        return type_name, node_id

    @staticmethod
    def get_pk(global_id: str, expected_type: str | None = None, raise_on_mismatch: bool = True) -> str:
        """Extract the PK from a global ID, optionally validating the type name."""
        type_name, pk = GlobalIDUtils.from_global_id(global_id)
        if expected_type and type_name != expected_type:
            if raise_on_mismatch:
                raise GraphQLError(
                    f"Invalid GlobalID: expected {expected_type}, got {type_name} "
                    f"(global_id: {global_id})"
                )
            return None
        return pk

    @staticmethod
    def get_pk_flexible(global_id: str, expected_type: str | None = None) -> str | None:
        """Extract PK from either a global ID or a raw integer string."""
        if not global_id:
            return None
        if isinstance(global_id, int) or global_id.isdigit():
            return str(global_id)
        return GlobalIDUtils.get_pk(global_id, expected_type=expected_type, raise_on_mismatch=False)

    @staticmethod
    def find_object_by_global_id(global_id: str, raise_not_found: bool = True):
        """Find any object by its global ID using the Graphene registry.

        Falls back to Django's ContentType framework to resolve the model.
        """
        from django.apps import apps
        type_name, pk = GlobalIDUtils.from_global_id(global_id)

        # Try to find the model by iterating registered models
        for model in apps.get_models():
            if model.__name__ == type_name or f'{model.__name__}Type' == type_name:
                instance = model.objects.filter(pk=pk).first()
                if instance:
                    return instance

        if raise_not_found:
            raise GraphQLError(f'Object {global_id} not found')
        return None


# ---------------------------------------------------------------------------
# Permission-filtered queryset helper
# ---------------------------------------------------------------------------

def permission_filtered_queryset(queryset: QuerySet, info: Info) -> QuerySet:
    """Apply the model's permission-based queryset filtering.

    Expects the model to implement:
        @classmethod
        def get_queryset(cls, queryset, user) -> QuerySet
    """
    model = queryset.model
    if hasattr(model, 'get_queryset'):
        return model.get_queryset(queryset, info.context.user)
    return queryset


# ---------------------------------------------------------------------------
# Case-insensitive ordering filter (for django-filter integration)
# ---------------------------------------------------------------------------

class CaseInsensitiveOrderingFilter(django_filters.OrderingFilter):
    """Ordering filter that sorts case-insensitively."""

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        from django.db.models.functions import Lower
        for param in value:
            if param.startswith('-'):
                qs = qs.order_by(Lower(param[1:])).reverse()
            else:
                qs = qs.order_by(Lower(param))
        return qs


# ---------------------------------------------------------------------------
# Simple standalone types (no Django model backing)
# ---------------------------------------------------------------------------

@strawberry.type(description="A named counter.")
class CounterType:
    id: str
    name: str
    count: int


@strawberry.type(description="A monetary amount with currency.")
class MoneyType:
    currency: str
    amount: str

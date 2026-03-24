"""Custom Strawberry GraphQL view with logging and caching.

Replaces core/utils/core_graph_ql_view.py (Graphene's CoreGraphQLView).
"""
from __future__ import annotations

import time

from strawberry.django.views import GraphQLView

from core.strawberry_schema.context import StrawberryContext


class CoreStrawberryView(GraphQLView):
    """Strawberry GraphQL view with request logging and context injection."""

    def get_context(self, request, response=None):
        return StrawberryContext(request)

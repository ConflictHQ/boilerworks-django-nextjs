"""GraphQL types and queries for the mutation audit log."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import strawberry
from strawberry.types import Info


@strawberry.type
class AuditLogEntry:
    operation: str
    variables: strawberry.scalars.JSON
    success: bool
    errors: list[str]
    ip_address: Optional[str]
    timestamp: datetime
    username: Optional[str]


@strawberry.type
class AuditLogQuery:

    @strawberry.field(description="Query mutation audit logs. Admin only.")
    def audit_logs(
        self, info: Info,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[AuditLogEntry]:
        from core.schema.audit import MutationAuditLog

        qs = MutationAuditLog.objects.select_related('user').order_by('-timestamp')
        if operation:
            qs = qs.filter(operation__icontains=operation)
        if user_id:
            qs = qs.filter(user_id=user_id)

        return [
            AuditLogEntry(
                operation=log.operation,
                variables=log.variables,
                success=log.success,
                errors=log.errors,
                ip_address=log.ip_address,
                timestamp=log.timestamp,
                username=log.user.username if log.user else None,
            )
            for log in qs[:limit]
        ]

"""GraphQL mutation audit log.

Strawberry extension that records every mutation execution:
who called it, when, with what variables, and whether it succeeded.

Sensitive fields (password, pin, token) are redacted from logged variables.
"""
import logging
from datetime import datetime
from typing import Any

from django.conf import settings
from django.db import models
from strawberry.extensions import SchemaExtension

from core.models import Tracking

logger = logging.getLogger(__name__)

SENSITIVE_KEYS = {'password', 'pin', 'token', 'secret', 'ssn', 'credit_card', 'secure'}


def _redact(variables: dict | None) -> dict:
    """Redact sensitive fields from mutation variables."""
    if not variables:
        return {}
    redacted = {}
    for key, value in variables.items():
        if any(s in key.lower() for s in SENSITIVE_KEYS):
            redacted[key] = '***REDACTED***'
        elif isinstance(value, dict):
            redacted[key] = _redact(value)
        else:
            redacted[key] = value
    return redacted


class MutationAuditLog(models.Model):
    """Persistent log of every GraphQL mutation execution."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mutation_audit_logs',
    )
    operation = models.CharField(max_length=200, db_index=True)
    variables = models.JSONField(default=dict, blank=True)
    success = models.BooleanField(default=True)
    errors = models.JSONField(default=list, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['operation', '-timestamp']),
        ]

    def __str__(self):
        return f'{self.operation} by {self.user} at {self.timestamp}'


class MutationAuditExtension(SchemaExtension):
    """Strawberry schema extension that logs mutations to the database."""

    def on_operation(self):
        yield  # Let the operation execute
        # After execution, log if it was a mutation
        try:
            request = self.execution_context
            if not request or not request.query:
                return

            query = request.query.strip()
            if not query.lower().startswith('mutation'):
                return

            # Extract operation name
            operation_name = request.operation_name or 'unknown'

            # Get user from context
            user = None
            ip_address = None
            context = getattr(request, 'context', None)
            if context:
                user = getattr(context, 'user', None)
                if user and not user.is_authenticated:
                    user = None
                req = getattr(context, 'request', None)
                if req:
                    ip_address = _get_client_ip(req)

            # Check for errors
            result = request.result
            has_errors = bool(result and result.errors)
            error_messages = []
            if has_errors and result.errors:
                error_messages = [str(e) for e in result.errors[:5]]

            # Redact sensitive variables
            variables = _redact(request.variables)

            MutationAuditLog.objects.create(
                user=user,
                operation=operation_name,
                variables=variables,
                success=not has_errors,
                errors=error_messages,
                ip_address=ip_address,
            )
        except Exception as e:
            logger.warning(f'Mutation audit log failed: {e}')


def _get_client_ip(request) -> str | None:
    """Extract client IP from Django request."""
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

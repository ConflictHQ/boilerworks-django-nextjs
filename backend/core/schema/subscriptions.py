"""Strawberry GraphQL subscriptions.

Provides real-time updates via WebSocket. Strawberry handles the WebSocket
protocol natively via its AsyncGenerator pattern.

Usage: connect to ws://localhost:8000/app/gql/config/ws/ with graphql-ws protocol.
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import strawberry
from strawberry.types import Info


@strawberry.type
class Subscription:

    @strawberry.subscription
    async def notification_received(self, info: Info) -> AsyncGenerator[str, None]:
        """Subscribe to new notifications for the current user.

        Yields notification subjects as they arrive.
        This is a polling-based implementation — replace with
        Redis PubSub or Django Channels for production.
        """
        from core.models import Notification
        last_id = None

        # Get initial last notification ID
        latest = Notification.objects.filter(
            user=info.context.user
        ).order_by('-created_at').first()
        if latest:
            last_id = latest.pk

        while True:
            await asyncio.sleep(2)  # Poll every 2 seconds
            try:
                qs = Notification.objects.filter(user=info.context.user).order_by('-created_at')
                if last_id:
                    qs = qs.filter(pk__gt=last_id)
                for notif in qs[:10]:
                    yield notif.subject
                    last_id = max(last_id or 0, notif.pk)
            except Exception:
                pass

    @strawberry.subscription
    async def form_submission_received(self, info: Info, slug: str) -> AsyncGenerator[str, None]:
        """Subscribe to new submissions for a specific form.

        Yields submission IDs as they arrive.
        """
        from forms.models import FormSubmission
        last_id = None

        latest = FormSubmission.objects.filter(
            form__slug=slug
        ).order_by('-submitted_at').first()
        if latest:
            last_id = latest.pk

        while True:
            await asyncio.sleep(2)
            try:
                qs = FormSubmission.objects.filter(form__slug=slug).order_by('-submitted_at')
                if last_id:
                    qs = qs.filter(pk__gt=last_id)
                for sub in qs[:10]:
                    yield f'New submission #{sub.pk}'
                    last_id = max(last_id or 0, sub.pk) if isinstance(sub.pk, int) else sub.pk
            except Exception:
                pass

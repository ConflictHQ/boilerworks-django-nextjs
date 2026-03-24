"""Strawberry batch load functions.

Each loader has a _sync version for direct use in sync contexts and tests,
plus an async wrapper for Strawberry's DataLoader.

Usage in resolvers:
    loader = info.context.get_loader('load_user_by_id', batch_load_users)
    user = await loader.load(user_id)
"""
from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.db.models import Count, F

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from core.models import Profile, Upload


# ---------------------------------------------------------------------------
# User loaders
# ---------------------------------------------------------------------------

def batch_load_users_sync(keys: list[int]) -> list[User | None]:
    users = {u.id: u for u in get_user_model().objects.filter(id__in=keys)}
    return [users.get(k) for k in keys]


async def batch_load_users(keys: list[int]) -> list[User | None]:
    return await sync_to_async(batch_load_users_sync)(keys)


# ---------------------------------------------------------------------------
# Profile loaders
# ---------------------------------------------------------------------------

def batch_load_profiles_by_gid_sync(keys: list[str]) -> list[Profile | None]:
    from core.models import Profile
    profiles = {
        p.gid: p
        for p in Profile.objects.filter(gid__in=keys)
        .select_related('avatar', 'signature', 'active_organization')
    }
    return [profiles.get(k) for k in keys]


async def batch_load_profiles_by_gid(keys: list[str]) -> list[Profile | None]:
    return await sync_to_async(batch_load_profiles_by_gid_sync)(keys)


def batch_load_profiles_by_user_id_sync(keys: list[int]) -> list[Profile | None]:
    from core.models import Profile
    profiles = {
        p.user_id: p
        for p in Profile.objects.filter(user_id__in=keys)
        .select_related('avatar', 'signature', 'active_organization')
    }
    return [profiles.get(k) for k in keys]


async def batch_load_profiles_by_user_id(keys: list[int]) -> list[Profile | None]:
    return await sync_to_async(batch_load_profiles_by_user_id_sync)(keys)


def batch_load_first_names_sync(keys: list[int]) -> list[str]:
    """Profile first_name takes precedence over User.first_name."""
    names = {k: '' for k in keys}
    for user in get_user_model().objects.filter(id__in=keys):
        names[user.id] = user.first_name or names[user.id]
    from core.models import Profile
    for profile in Profile.objects.filter(user_id__in=keys):
        names[profile.user_id] = profile.first_name or names[profile.user_id]
    return [names[k] for k in keys]


async def batch_load_first_names(keys: list[int]) -> list[str]:
    return await sync_to_async(batch_load_first_names_sync)(keys)


def batch_load_last_names_sync(keys: list[int]) -> list[str]:
    """Profile last_name takes precedence over User.last_name."""
    names = {k: '' for k in keys}
    for user in get_user_model().objects.filter(id__in=keys):
        names[user.id] = user.last_name or names[user.id]
    from core.models import Profile
    for profile in Profile.objects.filter(user_id__in=keys):
        names[profile.user_id] = profile.last_name or names[profile.user_id]
    return [names[k] for k in keys]


async def batch_load_last_names(keys: list[int]) -> list[str]:
    return await sync_to_async(batch_load_last_names_sync)(keys)


# ---------------------------------------------------------------------------
# Upload loader
# ---------------------------------------------------------------------------

def batch_load_uploads_sync(keys: list[int]) -> list[Upload | None]:
    from core.models import Upload
    uploads = {u.id: u for u in Upload.objects.filter(id__in=keys)}
    return [uploads.get(k) for k in keys]


async def batch_load_uploads(keys: list[int]) -> list[Upload | None]:
    return await sync_to_async(batch_load_uploads_sync)(keys)


# ---------------------------------------------------------------------------
# Library count loaders
# ---------------------------------------------------------------------------

def batch_load_file_counts_sync(keys: list[int]) -> list[int]:
    from core.models import SharedFile
    counts = defaultdict(int)
    for row in (
        SharedFile.objects
        .filter(parent_id__in=keys)
        .values('parent_id')
        .annotate(count=Count('parent_id'))
    ):
        counts[row['parent_id']] = row['count']
    return [counts[k] for k in keys]


async def batch_load_file_counts(keys: list[int]) -> list[int]:
    return await sync_to_async(batch_load_file_counts_sync)(keys)


def batch_load_directory_counts_sync(keys: list[int]) -> list[int]:
    from core.models import SharedDirectory
    counts = defaultdict(int)
    for row in (
        SharedDirectory.objects
        .filter(parent_id__in=keys)
        .values('parent_id')
        .annotate(count=Count('parent_id'))
    ):
        counts[row['parent_id']] = row['count']
    return [counts[k] for k in keys]


async def batch_load_directory_counts(keys: list[int]) -> list[int]:
    return await sync_to_async(batch_load_directory_counts_sync)(keys)


# ---------------------------------------------------------------------------
# Active user info loader (complex — combines org, membership, dept)
# ---------------------------------------------------------------------------

def batch_load_active_by_user_id_sync(keys: list[int], context) -> list:
    """Returns a list of dicts with organization, membership, and department_employees."""
    from organization.models import OrganizationMember

    org_cache = context._organization_cache

    memberships = {
        m.member_id: m
        for m in OrganizationMember.objects.filter(
            member_id__in=keys,
            organization=context.organization,
        )
        if m.is_active
    }

    organizations = {
        member_id: org_cache.get(m.organization_id)
        for member_id, m in memberships.items()
    }

    membership_ids = [m.id for m in memberships.values()]
    department_employees = defaultdict(list)

    try:
        from domain_app.models import DepartmentEmployee
        for de in (
            DepartmentEmployee.objects
            .filter(employee__membership__id__in=membership_ids)
            .annotate(user_id=F('employee__membership__member__id'))
            .prefetch_related('employee')
        ):
            department_employees[de.user_id].append(de)
    except ImportError:
        pass  # domain_app not installed

    results = []
    for user_id in keys:
        if user_id in memberships:
            results.append({
                'organization': organizations.get(user_id),
                'membership': memberships.get(user_id),
                'department_employees': department_employees.get(user_id, []),
            })
        else:
            results.append(None)
    return results


async def batch_load_active_by_user_id(keys: list[int], context) -> list:
    return await sync_to_async(batch_load_active_by_user_id_sync)(keys, context)

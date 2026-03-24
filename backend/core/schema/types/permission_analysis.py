"""Permission analysis and debugging types and queries.

Provides tools to diagnose why a user can or can't perform an action,
compare permissions between users, and list effective permissions.
"""
from __future__ import annotations

from typing import Optional

import strawberry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from strawberry.types import Info

User = get_user_model()


@strawberry.type
class PermissionEntry:
    """A single permission with its source (which group grants it)."""
    codename: str
    name: str
    app_label: str
    model: str
    granted_via_groups: list[str]


@strawberry.type
class PermissionTraceStep:
    """One step in a permission diagnosis trace."""
    check: str
    result: bool
    detail: str


@strawberry.type
class PermissionDiagnosis:
    """Full diagnosis of why a user can or can't perform an action."""
    user_id: strawberry.ID
    username: str
    permission: str
    granted: bool
    is_superuser: bool
    steps: list[PermissionTraceStep]


@strawberry.type
class PermissionDiff:
    """A permission that differs between two users."""
    codename: str
    name: str
    user_a_has: bool
    user_b_has: bool


@strawberry.type
class PermissionComparison:
    """Side-by-side permission comparison between two users."""
    user_a_username: str
    user_b_username: str
    only_a: list[str]
    only_b: list[str]
    shared: list[str]
    differences: list[PermissionDiff]


def _get_user_effective_permissions(user: User) -> dict[str, list[str]]:
    """Get all permissions a user has, mapped to the groups that grant them.

    Returns dict of codename → [group_names].
    """
    if user.is_superuser:
        # Superusers have all permissions
        result = {}
        for perm in Permission.objects.select_related('content_type').all():
            result[perm.codename] = ['superuser']
        return result

    # Get groups the user belongs to (scoped to their active org)
    try:
        org = user.profile.organization()
        user_groups = user.groups.filter(memberships__organization=org)
    except Exception:
        user_groups = user.groups.all()

    result = {}
    for group in user_groups.prefetch_related('permissions', 'permissions__content_type'):
        for perm in group.permissions.all():
            if perm.codename not in result:
                result[perm.codename] = []
            result[perm.codename].append(group.name)

    return result


def _get_user_permission_codenames(user: User) -> set[str]:
    """Get flat set of permission codenames for a user."""
    return set(_get_user_effective_permissions(user).keys())


@strawberry.type
class PermissionAnalysisQuery:
    """Permission analysis and debugging queries."""

    @strawberry.field(description="List all effective permissions for a user, with the groups that grant each one.")
    def effective_permissions(self, info: Info, user_id: strawberry.ID) -> list[PermissionEntry]:
        from core.schema.common import GlobalIDUtils
        pk = GlobalIDUtils.get_pk_flexible(user_id)
        user = User.objects.filter(pk=pk).first()
        if not user:
            return []

        perm_map = _get_user_effective_permissions(user)
        entries = []
        for perm in Permission.objects.select_related('content_type').filter(codename__in=perm_map.keys()):
            entries.append(PermissionEntry(
                codename=perm.codename,
                name=perm.name,
                app_label=perm.content_type.app_label,
                model=perm.content_type.model,
                granted_via_groups=perm_map.get(perm.codename, []),
            ))
        return entries

    @strawberry.field(description="Diagnose why a user can or can't perform a specific permission.")
    def permission_diagnose(
        self, info: Info, user_id: strawberry.ID, permission: str
    ) -> Optional[PermissionDiagnosis]:
        from core.schema.common import GlobalIDUtils
        pk = GlobalIDUtils.get_pk_flexible(user_id)
        user = User.objects.filter(pk=pk).first()
        if not user:
            return None

        steps = []
        granted = False

        # Step 1: Is user authenticated?
        steps.append(PermissionTraceStep(
            check='is_authenticated',
            result=user.is_authenticated,
            detail=f'User {user.username} is {"" if user.is_authenticated else "NOT "}authenticated',
        ))

        if not user.is_authenticated:
            return PermissionDiagnosis(
                user_id=str(user.pk), username=user.username,
                permission=permission, granted=False,
                is_superuser=False, steps=steps,
            )

        # Step 2: Is user superuser?
        steps.append(PermissionTraceStep(
            check='is_superuser',
            result=user.is_superuser,
            detail=f'User {user.username} is {"" if user.is_superuser else "NOT "}a superuser',
        ))

        if user.is_superuser:
            return PermissionDiagnosis(
                user_id=str(user.pk), username=user.username,
                permission=permission, granted=True,
                is_superuser=True, steps=steps,
            )

        # Step 3: Check active organization
        try:
            org = user.profile.organization()
            has_org = org is not None
            steps.append(PermissionTraceStep(
                check='has_active_organization',
                result=has_org,
                detail=f'Active organization: {org.name if org else "None"}',
            ))
        except Exception as e:
            steps.append(PermissionTraceStep(
                check='has_active_organization',
                result=False,
                detail=f'Error getting organization: {str(e)}',
            ))
            return PermissionDiagnosis(
                user_id=str(user.pk), username=user.username,
                permission=permission, granted=False,
                is_superuser=False, steps=steps,
            )

        # Step 4: Check group memberships in the org
        org_groups = user.groups.filter(memberships__organization=org)
        group_names = list(org_groups.values_list('name', flat=True))
        steps.append(PermissionTraceStep(
            check='org_group_memberships',
            result=len(group_names) > 0,
            detail=f'Groups in org "{org.name}": {", ".join(group_names) if group_names else "NONE"}',
        ))

        # Step 5: Check if any group has the permission
        perm_obj = Permission.objects.filter(codename=permission).first()
        if not perm_obj:
            # Try codename format: app_label.codename
            if '.' in permission:
                app_label, codename = permission.rsplit('.', 1)
                perm_obj = Permission.objects.filter(
                    codename=codename,
                    content_type__app_label=app_label,
                ).first()

        if not perm_obj:
            steps.append(PermissionTraceStep(
                check='permission_exists',
                result=False,
                detail=f'Permission "{permission}" not found in database',
            ))
            return PermissionDiagnosis(
                user_id=str(user.pk), username=user.username,
                permission=permission, granted=False,
                is_superuser=False, steps=steps,
            )

        steps.append(PermissionTraceStep(
            check='permission_exists',
            result=True,
            detail=f'Permission found: {perm_obj.content_type.app_label}.{perm_obj.codename} ({perm_obj.name})',
        ))

        # Step 6: Which groups have this permission?
        groups_with_perm = Group.objects.filter(permissions=perm_obj)
        groups_with_perm_names = list(groups_with_perm.values_list('name', flat=True))
        steps.append(PermissionTraceStep(
            check='groups_with_permission',
            result=len(groups_with_perm_names) > 0,
            detail=f'Groups that have "{permission}": {", ".join(groups_with_perm_names) if groups_with_perm_names else "NONE"}',
        ))

        # Step 7: Does the user's org groups intersect with permission groups?
        matching_groups = org_groups.filter(permissions=perm_obj)
        matching_names = list(matching_groups.values_list('name', flat=True))
        granted = len(matching_names) > 0
        steps.append(PermissionTraceStep(
            check='user_org_groups_have_permission',
            result=granted,
            detail=f'User\'s org groups with this permission: {", ".join(matching_names) if matching_names else "NONE — PERMISSION DENIED"}',
        ))

        return PermissionDiagnosis(
            user_id=str(user.pk), username=user.username,
            permission=permission, granted=granted,
            is_superuser=False, steps=steps,
        )

    @strawberry.field(description="Compare effective permissions between two users.")
    def permission_compare(
        self, info: Info, user_id_a: strawberry.ID, user_id_b: strawberry.ID
    ) -> Optional[PermissionComparison]:
        from core.schema.common import GlobalIDUtils
        pk_a = GlobalIDUtils.get_pk_flexible(user_id_a)
        pk_b = GlobalIDUtils.get_pk_flexible(user_id_b)
        user_a = User.objects.filter(pk=pk_a).first()
        user_b = User.objects.filter(pk=pk_b).first()
        if not user_a or not user_b:
            return None

        perms_a = _get_user_permission_codenames(user_a)
        perms_b = _get_user_permission_codenames(user_b)

        only_a = sorted(perms_a - perms_b)
        only_b = sorted(perms_b - perms_a)
        shared = sorted(perms_a & perms_b)

        differences = []
        for codename in sorted(perms_a.symmetric_difference(perms_b)):
            perm = Permission.objects.filter(codename=codename).first()
            if perm:
                differences.append(PermissionDiff(
                    codename=codename,
                    name=perm.name,
                    user_a_has=codename in perms_a,
                    user_b_has=codename in perms_b,
                ))

        return PermissionComparison(
            user_a_username=user_a.username,
            user_b_username=user_b.username,
            only_a=only_a,
            only_b=only_b,
            shared=shared,
            differences=differences,
        )

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

import strawberry
import strawberry_django
from django.conf import settings
from django.contrib.auth import get_user_model
from strawberry.types import Info

from core.models import PinTransaction, Profile, SignRequest, UserSwitchGroup
from core.schema.common import permission_filtered_queryset
from core.schema.dataloaders import (
    batch_load_first_names,
    batch_load_last_names,
    batch_load_profiles_by_user_id,
    batch_load_uploads,
)
from core.schema.types.upload import UploadType

try:
    from domain_app.models import DepartmentEmployee, Employee
    HAS_DOMAIN_APP = True
except ImportError:
    DepartmentEmployee = None
    Employee = None
    HAS_DOMAIN_APP = False

User = get_user_model()


# ---------------------------------------------------------------------------
# ActiveType — complex nested type for user's active org/membership/dept
# ---------------------------------------------------------------------------

@strawberry.type
class ActiveType:
    organization: Optional[strawberry.scalars.JSON] = None
    membership: Optional[strawberry.scalars.JSON] = None


# ---------------------------------------------------------------------------
# PinTransactionType
# ---------------------------------------------------------------------------

@strawberry_django.type(PinTransaction)
class PinTransactionType:

    @strawberry_django.field(
        description="Effective creation timestamp. Returns created_at_override if set, otherwise created_at."
    )
    def created_at(self) -> datetime:
        return self.effective_created_at


# ---------------------------------------------------------------------------
# SignRequestType
# ---------------------------------------------------------------------------

@strawberry_django.type(SignRequest)
class SignRequestType:

    @strawberry_django.field
    def users_allowed_to_sign(self, info: Info) -> list[UserType]:
        return self.users_allowed_to_sign()


# ---------------------------------------------------------------------------
# UserSwitchType
# ---------------------------------------------------------------------------

@strawberry_django.type(UserSwitchGroup)
class UserSwitchType:
    pass


# ---------------------------------------------------------------------------
# ProfileType — heavy permission checks on every field
# ---------------------------------------------------------------------------

@strawberry_django.type(Profile)
class ProfileType:
    guid: UUID
    display_name: Optional[str]
    nickname: Optional[str]
    birth_date: Optional[datetime]
    preferred_language: Optional[str]
    timezone: Optional[str]
    is_active: bool

    @strawberry_django.field(description="Direct reference to User.email.")
    def email(self, info: Info) -> Optional[str]:
        if Profile.p('email').view.by(info.context.user):
            return self.user.email
        return None

    @strawberry_django.field
    def first_name(self, info: Info) -> Optional[str]:
        if info.context.check_permission(
            f"Profile.p('first_name').view.by({info.context.user.id})",
            lambda: Profile.p('first_name').view.by(info.context.user),
        ):
            return self.first_name
        return None

    @strawberry_django.field
    def last_name(self, info: Info) -> Optional[str]:
        if info.context.check_permission(
            f"Profile.p('last_name').view.by({info.context.user.id})",
            lambda: Profile.p('last_name').view.by(info.context.user),
        ):
            return self.last_name
        return None

    @strawberry_django.field
    def username(self, info: Info) -> Optional[str]:
        return self.user.username

    @strawberry_django.field
    def has_pin(self) -> bool:
        return self.pin is not None and self.pin != ''

    @strawberry_django.field
    async def avatar(self, info: Info) -> Optional[UploadType]:
        if info.context.check_permission(
            f"Profile.p('avatar').view.by({info.context.user.id})",
            lambda: Profile.p('avatar').view.by(info.context.user),
        ):
            if self.avatar_id:
                loader = info.context.get_loader('load_upload_by_id', batch_load_uploads)
                return await loader.load(self.avatar_id)
        return None

    @strawberry_django.field
    async def signature(self, info: Info) -> Optional[UploadType]:
        if info.context.check_permission(
            f"Profile.p('signature').view.by({info.context.user.id})",
            lambda: Profile.p('signature').view.by(info.context.user),
        ):
            if self.signature_id:
                loader = info.context.get_loader('load_upload_by_id', batch_load_uploads)
                return await loader.load(self.signature_id)
        return None


# ---------------------------------------------------------------------------
# UserType — the central type, heavy dataloader usage
# ---------------------------------------------------------------------------

@strawberry_django.type(User)
class UserType:
    is_anonymous: bool
    email: str

    @strawberry_django.field
    def is_new_user(self, info: Info) -> bool:
        return self.profile.is_new_user()

    @strawberry_django.field
    async def first_name(self, info: Info) -> str:
        if info.context.check_permission(
            f"Profile.p('first_name').view.by({info.context.user.id})",
            lambda: Profile.p('first_name').view.by(info.context.user),
        ):
            loader = info.context.get_loader('load_first_names', batch_load_first_names)
            return await loader.load(self.id)
        return ''

    @strawberry_django.field
    async def last_name(self, info: Info) -> str:
        if info.context.check_permission(
            f"Profile.p('last_name').view.by({info.context.user.id})",
            lambda: Profile.p('last_name').view.by(info.context.user),
        ):
            loader = info.context.get_loader('load_last_names', batch_load_last_names)
            return await loader.load(self.id)
        return ''

    @strawberry_django.field
    async def profile(self, info: Info) -> Optional[ProfileType]:
        loader = info.context.get_loader('load_profiles_by_user_id', batch_load_profiles_by_user_id)
        return await loader.load(self.id)

    @strawberry.field
    def memberships(self, info: Info) -> list[strawberry.scalars.JSON]:
        """User's organization memberships. Returns raw membership data."""
        user = self
        main_user_pk = info.context.session.get('main_user_pk', user.pk)
        if main_user_pk != user.pk:
            user = User.objects.filter(pk=main_user_pk).first()
        return list(user.memberships.values('id', 'organization_id', 'is_active'))

    @strawberry_django.field
    def username(self, info: Info) -> str:
        return self.username

    @strawberry_django.field
    def employee_id(self, info: Info) -> Optional[str]:
        if self.username == settings.API_SYSTEM_USER:
            return None
        if not HAS_DOMAIN_APP:
            return None
        employee = Employee.objects.first_user(self)
        return employee.global_id() if employee else None

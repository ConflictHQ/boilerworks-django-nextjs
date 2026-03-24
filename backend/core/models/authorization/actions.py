from core.models.enum import BaseEnumModel, register_for_model
from django.db import models

from ..enum import EnumModel


class SharedResourcePermission(EnumModel):
    code = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=64, unique=True)


@register_for_model(SharedResourcePermission)
class SharedFilePermissions(BaseEnumModel):

    DENY = SharedResourcePermission.Literal(
        code='deny',
        name='Deny'
    )

    READ = SharedResourcePermission.Literal(
        code='read',
        name='Read'
    )

    WRITE = SharedResourcePermission.Literal(
        code='write',
        name='Write'
    )

    DOWNLOAD = SharedResourcePermission.Literal(
        code='download',
        name='Download'
    )

    SHARE = SharedResourcePermission.Literal(
        code='share',
        name='Share'
    )

    MANAGE = SharedResourcePermission.Literal(
        code='manage',
        name='Manage'
    )

    @classmethod
    def default_action(cls) -> "SharedFilePermissions":
        return SharedFilePermissions.DENY

    @classmethod
    def owners_action(cls) -> "SharedFilePermissions":
        return SharedFilePermissions.MANAGE


__all__ = [
    'SharedFilePermissions'
]

import logging
from functools import wraps

from config.roles_gen import P
from django.contrib.auth.models import Permission

logger = logging.getLogger(__name__)


class AllPermissions:
    permissions = {}

    @classmethod
    def reset(cls):
        cls.permissions = {}

    @classmethod
    def p_to_id(cls, p):
        return f'{p.content_type.model}.{p.codename}'

    @classmethod
    def load_permissions(cls, name=None) -> 'AllPermissions':
        if name and len(cls.permissions) > 0:
            model, codename = name.split('.')
            cls.permissions[name] = Permission.objects.filter(content_type__model=model, codename=codename).first()
            if not cls.permissions[name]:
                logger.warning(f'Permission {name} not found. Generate permissions!!!!')
        else:
            cls.permissions = {cls.p_to_id(p): p for p in Permission.objects.select_related('content_type').all()}
        return cls

    @classmethod
    def get(cls, name) -> Permission:
        if name not in cls.permissions:
            cls.load_permissions(name)

        return cls.permissions.get(name)

    @classmethod
    def to_perm(cls, p) -> Permission:
        return AllPermissions.get(p.value)


def permission_silence_check(permission: P, return_value=None):
    def request_decorator(dispatch):
        @wraps(dispatch)
        def wrapper(root, info, *args, **kwargs):
            if permission.by(info.context.user):
                return dispatch(root, info, *args, **kwargs)

            if callable(return_value):
                return return_value()
            return return_value

        return wrapper

    return request_decorator

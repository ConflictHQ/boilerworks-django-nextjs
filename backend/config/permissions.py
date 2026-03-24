import dataclasses
import logging
from datetime import timedelta
from typing import Type

from core.models import Tracking
from core.utils.performance import cache_class_method
from core_logs.models import PermissionAccessLog
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


def permission_checker(perm):
    def wrapped_decorator(func):
        def wrapped_mutation(cls, root, info, **input):
            # make sure of these arguments to the wrapped mutations
            user = info.context.user
            perms = (perm, ) if isinstance(perm, str) else perm

            if user.has_perms(perms):
                return func(cls, root, info, **input)

            raise PermissionDenied("Permission Denied.")
        return wrapped_mutation
    return wrapped_decorator


MAP_P_TO_PERM = {}
MAP_PERM_TO_P = {}


class AbstractPermissions:

    @classmethod
    def denied(cls, user, value, msg=None, permission=None):
        if settings.DEBUG:
            msg = msg or f'User {user.username} has not \'{value}\'. Organization: {user.profile.organization()}.'
            PermissionAccessLog.log_denied(user, permission=permission, msg=msg, raise_error=True)
            raise PermissionDenied(msg)

        codename = value
        if permission is not None:
            codename = f"{permission.content_type.app_label}.{permission.content_type.model}_{permission.codename}"

        match settings.CONFIGURATION:
            case 'Tests':
                msg = f'User does not have required permissions: {codename}'
            case _:
                msg = msg or 'User does not have required permissions.'

        PermissionAccessLog.log_denied(user, permission=permission, msg=msg, raise_error=True)
        raise PermissionDenied(msg)

    def log_granted(self, user, msg=None):
        return PermissionAccessLog.log_granted(user, self.perm(), msg)

    def log_used_in_filter(self, user):
        return PermissionAccessLog.log_used_in_filter(user, self.perm())

    def log_denied(self, user, raised_error=True, msg=None):
        return PermissionAccessLog.log_denied(user, self.perm(), msg, raised_error)

    def check(self, user, raised_error=True):
        if not user.is_authenticated:
            msg = 'Indirect error. User is not authenticated'
            if raised_error:
                self.denied(user, None, msg=msg, permission=self.perm())
            self.log_denied(user, False, msg=msg)

        if user.is_superuser:
            self.log_granted(user)
            return True

        if not self.by(user):
            if raised_error:
                self.denied(user, self.perm().name, permission=self.perm())
            self.log_denied(user, False)
            return False

        self.log_granted(user)
        return True

    @classmethod
    def check_django_auth_permission(cls, user: User, model: str, action, raised_error=True):
        app = 'auth'
        from core.systems import Action
        action: Action
        permission = Permission.objects.get(codename=f'{action.value}_{model}',
                                            content_type=ContentType.objects.get(app_label=app, model=model))
        if not user.is_authenticated:
            msg = 'Indirect error. User is not authenticated'
            if raised_error:
                cls.denied(user, None, msg=msg, permission=permission)
            PermissionAccessLog.log_denied(user, permission, msg, raised_error)

        codename = f'{app}.{action.value}_{model}'
        if not user.has_perm(codename):
            if raised_error:
                cls.denied(user, permission.name, msg=None, permission=permission)
            PermissionAccessLog.log_denied(user, permission, raise_error=True)

        PermissionAccessLog.log_granted(user, permission)
        return True

    def by(self, user) -> bool:
        return self.allowed_filter(user)

    def allowed_filter(self, user) -> bool:
        if not user.is_authenticated:
            self.log_denied(user, True, 'Indirect error. User is not authenticated')
            raise PermissionDenied('User is not authenticated')

        if user.is_superuser:
            return True

        return self._allowed(user)

    @cache_class_method(timeout=timedelta(minutes=2), key_gen=lambda self,
                        user: f'p{self.perm().pk}u{user.pk}', cache_name='memory_cache')
    def _allowed(self, user) -> bool:
        """
        this method is cached to improve performance. What it is doing is to check if the user has the permission
        to access the data in the organization. If the user has the permission, it will return True, otherwise False.
        """
        allowed = user.groups.filter(
            memberships__organization=user.profile.organization(),
            permissions=self.perm(),
        ).exists()

        if allowed:
            self.log_granted(user, msg=f'Query: User {user.username} has {self.value}. '
                                       f'Organization: {user.profile.organization()}.')
        else:
            self.log_denied(user, False, f'Query: User {user.username} '
                                         f'has NOT {self.value}. Organization: {user.profile.organization()}.')

        return allowed

    def perm(self):
        if self not in MAP_P_TO_PERM:
            from core.systems.permissions import AllPermissions
            MAP_P_TO_PERM[self] = AllPermissions.get(self.value)
            MAP_PERM_TO_P[MAP_P_TO_PERM[self]] = self
        return MAP_P_TO_PERM.get(self)

    @classmethod
    def perm_to_enum(cls, p: Permission):
        from .roles_gen import P
        if p in MAP_PERM_TO_P:
            return MAP_PERM_TO_P[p]

        for e in P:
            if e.perm() == p:
                MAP_P_TO_PERM[p] = e
                MAP_PERM_TO_P[e] = p
                return e
        return None


class PPermission(AbstractPermissions):
    def __init__(self, permission: Permission):
        from core.systems.permissions import AllPermissions
        self.value = AllPermissions.p_to_id(permission)


@dataclasses.dataclass
class FieldPermissions:
    name: str
    view: AbstractPermissions = None
    add: AbstractPermissions = None
    change: AbstractPermissions = None
    delete: AbstractPermissions = None
    merge: AbstractPermissions = None
    approve: AbstractPermissions = None

    def can_view(self, user):
        return self._can(self.view, user)

    def can_add(self, user):
        return self._can(self.add, user)

    def can_delete(self, user):
        return self._can(self.delete, user)

    def can_change(self, user):
        return self._can(self.change, user)

    def _can(self, perm: AbstractPermissions, user):
        # Superusers bypass all permission checks
        if user and user.is_authenticated and user.is_superuser:
            return True
        # If no permission is configured, deny access
        if not perm:
            return False
        return perm and perm.by(user)


@dataclasses.dataclass
class ModelPermissions:
    model: Type[Tracking]
    permissions_map: dict[str, FieldPermissions] = dataclasses.field(default_factory=dict)
    permissions: [FieldPermissions] = dataclasses.field(default_factory=list)

    def __post_init__(self):
        """
        TODO cache this to improve performance
        :return:
        """
        content_type = ContentType.objects.get_for_model(self.model)
        permissions = Permission.objects.filter(content_type=content_type)

        fields_map = {}
        warnings = []

        for permission in permissions:
            codename = permission.codename
            try:
                perm_type, *name_parts = codename.split('_')
                field_name = '_'.join(name_parts)
                permission_enum = AbstractPermissions.perm_to_enum(permission)

                # Use setdefault to initialize perms if not present
                fields_map.setdefault(field_name, {})[perm_type.lower()] = permission_enum

            except ValueError as e:
                warnings.append(f"Failed to parse codename '{codename}': {str(e)}")
                logger.exception(f"Exception parsing codename '{codename}'", exc_info=e)

        # Construct FieldPermissions objects and populate permissions map
        for name, perms in fields_map.items():
            try:
                field_permission = FieldPermissions(name.lower(), **perms)
                self.permissions.append(field_permission)

                if name.lower() == self.model.__name__.lower():
                    self.permissions_map['model'] = field_permission
                else:
                    self.permissions_map[name.lower()] = field_permission

            except TypeError as e:
                warnings.append(f"Failed to create FieldPermissions for '{name}': {str(e)}")
                logger.error(f"Error creating FieldPermissions for '{name}'", exc_info=e)

        # Ensure the model itself has a permission entry
        if 'model' not in self.permissions_map:
            self.permissions_map['model'] = FieldPermissions(self.model.__name__.lower())
            logger.warning(
                f"Model {self.model.__name__} has no permissions! "
                f"Fields map: {fields_map}. Warnings: {warnings}"
            )

    def name(self):
        return self.model.__name__.lower()

    def element(self, name):
        return self.permissions_map[name]

    def view(self) -> AbstractPermissions:
        return self.permissions_map[self.name()].view

    def add(self,) -> AbstractPermissions:
        return self.permissions_map[self.name()].add

    def change(self) -> AbstractPermissions:
        return self.permissions_map[self.name()].change

    def delete(self) -> AbstractPermissions:
        return self.permissions_map[self.name()].delete

    def __getitem__(self, name):
        if name not in self.permissions_map:
            logger.warning(f'Field {name} not found in {self.model.__name__} permissions')
            return FieldPermissions(name)
        return name in self.permissions_map and self.permissions_map[name] or FieldPermissions(name)

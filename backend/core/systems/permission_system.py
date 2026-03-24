import logging
from enum import Enum

import django.apps
from django.apps import apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class Action(Enum):
    ADD = 'add'
    CHANGE = 'change'
    DELETE = 'delete'
    VIEW = 'view'


class ActionRecord:
    def __init__(self, permission: Permission, parent: 'PermissionCategory', action: Action, ):
        self.parent = parent
        self.permission = permission
        self.action = action

    @property
    def code_name(self):
        return self.permission.codename

    @property
    def name(self):
        return self.permission.name


class PermissionCategory:
    def __init__(self, parent, name):
        self.parent = parent
        self.name = name
        self.categories = {}
        self.actions = {}

    def get_category(self, name):
        if name not in self.categories:
            self.categories.update({name: PermissionCategory(self, name)})
        return self.categories[name]

    def add_action(self, permission, action: Action):
        if action not in self.actions:
            action_record = ActionRecord(permission, self, action)
            self.actions.update({action: action_record})

        return self.actions[action]


class PermissionSystem:
    """
    Do not use this class directly, create a Proxy instead (see PropertyPermissionSystem)
    The goal of the Proxy is to facilitate the transition to a remote permission system.
    """

    root = None
    actions = {}

    @classmethod
    def check_permissions(cls, assigned_permissions):
        if assigned_permissions.assignable_permissions.group and assigned_permissions.permissions.count() > 0:
            raise ValidationError(f'Assignable Permissions {assigned_permissions.assignable_permissions} is a group. '
                                  f'Permissions must be empty')
        elif assigned_permissions.permissions.count() == 0:
            raise ValidationError(f'Permissions must contains at least one permission from '
                                  f'Assignable Permissions {assigned_permissions.assignable_permissions}')
        else:
            error = ''
            for p in assigned_permissions.permissions.all():
                if not assigned_permissions.assignable_permissions.permissions.filter(pk=p.pk).exists():
                    error += f'Permission {p} is not in Assignable Permissions ' \
                             f'{assigned_permissions.assignable_permissions}\n'
            if error:
                raise ValidationError(error)

    @classmethod
    def _crete_path(cls, parent: PermissionCategory, path):
        if len(path):
            new_group = parent.get_category(path[0])
            return cls._crete_path(new_group, path[1:])
        else:
            return parent

    @classmethod
    def permissions_groups(cls):
        return django.apps.apps.get_models()

    @classmethod
    def permissions_categories(cls):
        # if PermissionSystem.root:
        #     return PermissionSystem.root

        PermissionSystem.root = PermissionCategory(None, 'root')
        for permission in Permission.objects.all():
            try:
                path = permission.codename.split('_')
                action = Action[path[0].upper()]
                content_type: ContentType = ContentType.objects.filter(pk=permission.content_type_id).first()
                model = apps.get_model(content_type.app_label, content_type.model)
                path[1] = model._meta.verbose_name.title()
                group = cls._crete_path(PermissionSystem.root, path[1:])
                action = group.add_action(permission, action)
                cls.actions[action.permission.id] = action
            except LookupError as e:
                logging.warning(f'Error parsing permission {e}')
            except Exception as e:
                logging.error(f'Error parsing permission {permission}', e)

        return PermissionSystem.root

    @classmethod
    def model_assignable_permissions(cls, model) -> QuerySet:
        cc = ContentType.objects.get_for_model(model)
        code_names = [codename for codename, _ in model._meta.permissions]
        return Permission.objects.filter(content_type=cc, codename__in=code_names)

    @classmethod
    def check(cls, is_ok, msg, console_msg, throw_error=True):
        if is_ok:
            return True
        else:
            logger.warning(console_msg)
            from core_logs.models import PermissionAccessLog
            PermissionAccessLog.log_denied(permission=msg)
            raise PermissionError(msg)

    @classmethod
    def check_model_assignable_permissions(cls, user, model, permissions_pk: list, throw_error=True):
        allowed = cls.model_assignable_permissions(model)
        count = allowed.filter(pk__in=permissions_pk).count()
        ok = count == len(permissions_pk)
        if ok or not throw_error:
            return count == len(permissions_pk)
        else:
            cls.check(False,
                      'Permissions not allowed',
                      f'Assignable Permissions not allowed model {model}, permissions list {permissions_pk}')

    @classmethod
    def assign(cls, permissions_pk=()):
        cls.check(False,
                  'Permissions not allowed',
                  f'Assignable Permissions not contains all {permissions_pk}')

    @classmethod
    def configure(cls, user, module, ref):
        return None


class Role:
    def __init__(self, group: Group):
        self.name = group.name
        self.group = group

    def permissions(self):
        return [PermissionSystem.actions[permission.id]
                for permission in self.group.permissions.all()]

    def users(self):
        return self.group.user_set.all()

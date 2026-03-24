import json
import logging
from datetime import timedelta
from typing import List, Optional

from core_logs.utils.error_helper import errors_to_str
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.db import models
from graphql import GraphQLError

logger = logging.getLogger(__name__)

logs = []


class AccessOptions(models.TextChoices):
    """
    Options for the access result
    """
    GRANTED = 'granted', 'Granted'
    DENIED = 'denied', 'Denied'
    USED_IN_FILTER = 'used_in_filter', 'Used in filter'
    DETAIL = 'detail', 'Detail of the result'


class PermissionAccessLog(models.Model):
    """
    Log of the permissions access
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, related_name='permissions_access_logs', editable=False)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, null=True, blank=True, editable=False)
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE,
                                     null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    access = models.CharField(max_length=20, choices=AccessOptions.choices, editable=False)
    raised_error = models.BooleanField(default=False, editable=False)
    description = models.TextField(blank=True, null=True, editable=False)

    class Meta:
        verbose_name = 'Permission Access Log'
        verbose_name_plural = 'Permission Access Logs'

    def __str__(self):
        return f'{self.user} - {self.permission}'

    def to_msg(self):
        permission = f' - {self.permission}' or ''
        return f'{self.organization}:{self.user}{permission} - {self.access} - {self.description}'

    @classmethod
    def log_denied(cls, user, permission: Permission = None, msg=None, raise_error=True):
        logs.append(dict(
            user=user,
            organization=user.profile.organization(),
            permission=cls._permission(permission),
            access=AccessOptions.DENIED,
            raised_error=raise_error,
            description=msg,
        ))

    @classmethod
    def log_detail(cls, user, permission: Permission = None, msg=None, raise_error=True):
        logs.append(dict(
            user=user,
            organization=user.profile.organization(),
            permission=cls._permission(permission),
            access=AccessOptions.DETAIL,
            raised_error=raise_error,
            description=msg,
        ))

    @classmethod
    def log_granted(cls, user, permission, msg=None):
        logs.append(dict(
            user=user,
            organization=user.profile.organization(),
            permission=cls._permission(permission),
            access=AccessOptions.GRANTED,
            description=msg,
        ))

    @classmethod
    def log_used_in_filter(cls, user, permission, msg=None):
        logs.append(dict(
            user=user,
            organization=user.profile.organization(),
            permission=cls._permission(permission),
            access=AccessOptions.USED_IN_FILTER,
            description=msg
        ))

    @classmethod
    def flush(cls):
        cls.objects.bulk_create([cls(**log) for log in logs])
        logs.clear()

    @classmethod
    def _permission(cls, permission: Permission):
        from config.permissions import AbstractPermissions
        if permission and isinstance(permission, (Permission, AbstractPermissions)):
            return permission.perm() if isinstance(permission, AbstractPermissions) else permission
        return None


class GQLLog(models.Model):
    """
    Log of the GraphQL queries
    """
    switch_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gql_logs',
                             editable=False)
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, editable=False)
    path = models.CharField(max_length=200, blank=True, null=True)

    operation_name = models.CharField(max_length=100, blank=True, null=True)
    platform = models.TextField(blank=True, null=True, max_length=100)
    variables = models.JSONField(blank=True, null=True)
    query = models.TextField(blank=True, null=True)

    body = models.TextField(blank=True, null=True)

    replayed_from = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    response = models.JSONField(blank=True, null=True, editable=False)
    error = models.TextField(blank=True, null=True, editable=False)

    duration_millis = models.IntegerField(blank=True, null=True, editable=False)

    class Meta:
        verbose_name = 'GQL Log'
        verbose_name_plural = 'GQL Logs'

    def __str__(self):
        return f'{self.user} - {self.created_at}'

    def to_msg(self):
        return f'{self.user} - {self.created_at}'

    @classmethod
    def log(cls,
            context,
            data,
            result=None,
            errors: Optional[List[GraphQLError]] = None,
            duration: timedelta = None,
            request_profiling=None):
        try:
            context.session.load()
            replayed_info = data.get('variables', {}).get('replayed_info', {})
            replayed_from = cls.objects.get(pk=replayed_info['from_log']) if replayed_info.get('from_log') else None

            switch_user = (
                    context.session.get(settings.SWITCHED_FROM_USER) or
                    replayed_info.get(settings.SWITCHED_FROM_USER)
            )

            if switch_user:
                switch_user = User.objects.get(pk=switch_user)

            variables = data.get('variables', {})

            if 'replayed_info' in variables:
                del variables['replayed_info']

            milliseconds = None
            if duration:
                total_seconds = duration.total_seconds()
                milliseconds = int(total_seconds * 1000)

            return cls.objects.create(
                switch_user=switch_user,
                user=context.user,
                path=context.path,
                organization=context.user.profile.organization(),
                variables=variables,
                query=data['query'],
                operation_name=data.get('operationName', 'undefined'),
                platform=context.headers.get('x-platform', None),
                body=context.body.decode('utf-8'),
                error=errors_to_str(errors) if errors else None,
                response=result.data if result else None,
                replayed_from=replayed_from,
                duration_millis=milliseconds
            )
        except Exception as e:
            logger.error(f'Error in GQLLog.log: {e}', exc_info=True)
            pass

    def execute(self, request, user=None):
        from django.test import Client
        user = user if user else self.user

        client = Client()
        client._login(user)

        body_json = json.loads(self.body)
        body_json['variables'] = {
            **self.variables,
            'replayed_info': {
                'from_log': self.id,
                'switched_from_user': request.session.get(
                    settings.SWITCHED_FROM_USER
                ),
            },
        }
        body_json['query'] = self.query

        response = client.post(self.path, data=body_json, content_type='application/json')
        return response

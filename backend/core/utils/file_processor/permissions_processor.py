import logging
from typing import Dict, List, Type

from core.models.process import DataProcessEntity, ProcessStatus
from core.systems import EntityProcessor
from core_logs.utils.error_helper import errors_to_str
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from organization.models import Organization

logger = logging.getLogger(__name__)


class PermissionsProcessor(EntityProcessor):
    allows_overwrite = True

    @classmethod
    def process(cls, records, user_id: Type[int], overwrite: bool = False) -> ProcessStatus:
        record: DataProcessEntity
        process_status = ProcessStatus.DONE
        for record in records:
            if not record.data:
                record.update_status(ProcessStatus.IGNORED)
                continue

            try:
                with transaction.atomic():
                    if overwrite:
                        Group.objects.all().delete()

                    for group_permissions in record.data:
                        permission_identifiers = []
                        for permission in group_permissions['permissions']:
                            permission_id = Permission.objects.filter(
                                content_type__app_label=permission['app_label'],
                                content_type__model=permission['model'],
                                codename=permission['codename']
                            ).values_list('id', flat=True).first()
                            if permission_id is None:
                                content_type_id = ContentType.objects.filter(
                                    app_label=permission['app_label'],
                                    model=permission['model']
                                ).values_list('id', flat=True).first()
                                if content_type_id is None:
                                    raise Exception(f'Content type {permission["app_label"]}.{permission["model"]} not found')
                                permission = Permission.objects.create(
                                    content_type_id=content_type_id,
                                    codename=permission['codename'],
                                    name=permission['permission_name']
                                )
                                permission_id = permission.id
                            permission_identifiers.append(permission_id)

                        if 'group' in group_permissions:
                            group, created = Group.objects.get_or_create(name=group_permissions['group'])
                            if created:
                                organization_id = Organization.objects.filter(
                                    slug=group_permissions['organization']
                                ).values_list('id', flat=True).first()
                                group.organizations.add(organization_id)
                            group.permissions.clear()
                            group.permissions.add(*permission_identifiers)
                            group.save()

                record.update_status(ProcessStatus.DONE)

            except Exception as e:
                logger.exception('Could not process permissions data', e)
                error_message = errors_to_str(e)
                process_status = ProcessStatus.FAILED
                record.update_status(ProcessStatus.FAILED, error_message)

        return process_status

    @classmethod
    def load_api_data(cls, process) -> List[Dict]:
        pass

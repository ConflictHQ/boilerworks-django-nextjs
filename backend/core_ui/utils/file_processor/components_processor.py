import logging
from typing import Dict, List, Type

from core.models.process import DataProcessEntity, ProcessStatus
from core.systems import EntityProcessor
from core.systems.permissions import AllPermissions
from core_logs.utils.error_helper import errors_to_str
from core_ui.models import Component, ComponentRelationship
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import DataError

logger = logging.getLogger(__name__)


class ComponentsProcessor(EntityProcessor):
    allows_overwrite = True

    @classmethod
    def process(cls, records, user_id: Type[int], overwrite: bool = False) -> ProcessStatus:
        logger.debug(f"Starting to process records: {len(records)}")
        record: DataProcessEntity
        process_status = ProcessStatus.DONE
        for record in records:
            if not record.data:
                record.update_status(ProcessStatus.IGNORED)
                continue

            try:
                with transaction.atomic():
                    if overwrite:
                        Component.objects.all().delete()
                        ComponentRelationship.objects.all().delete()

                    for component_entry in record.data:
                        if not component_entry.get('Slug'):
                            raise ValidationError(
                                'Missing Slug',
                                params={'value': component_entry},
                            )
                        component, _ = Component.objects.get_or_create(slug=component_entry.get('Slug'))

                        component.name = component_entry.get('Name')
                        component.is_active = component_entry.get('Is Active')
                        component.path = component_entry.get('Path')
                        component.icon = component_entry.get('Icon')
                        component.properties = component_entry.get('Properties')
                        component.description = component_entry.get('Description')
                        component.save()

                    for component_entry in record.data:
                        component = Component.objects.get(slug=component_entry.get('Slug'))

                        component.permissions.clear()
                        permissions = []
                        for permission in component_entry.get('Permissions'):
                            codename = f"""{permission['app_label']}.{permission['model']}_{permission['codename']}"""
                            permission = Permission.objects.filter(
                                content_type__app_label=permission['app_label'],
                                content_type__model=permission['model'],
                                codename=permission['codename']
                            ).values_list('id', flat=True).first()
                            if permission is None:
                                raise ValidationError(
                                    f'Permission not found: {codename}',
                                    params={'value': permission},
                                )
                            permissions.append(permission)
                        component.permissions.add(*permissions)

                        ComponentRelationship.objects.filter(parent=component).delete()
                        component.components.clear()
                        for child in component_entry.get('Children'):
                            child_component = Component.objects.get(slug=child['slug'])
                            ComponentRelationship.objects.create(
                                parent=component,
                                child=child_component,
                                order=child['order']
                            )

                        component.created_by_id = user_id
                        component.updated_by_id = user_id
                        component.save()

                        AllPermissions.reset()
                record.update_status(ProcessStatus.DONE)
            except (Exception, ValidationError, DataError) as e:
                logger.exception('Could not process components data', e)
                error_message = errors_to_str(e)
                process_status = ProcessStatus.FAILED
                record.update_status(ProcessStatus.FAILED, error_message)

        return process_status

    @classmethod
    def load_api_data(cls, process) -> List[Dict]:
        pass

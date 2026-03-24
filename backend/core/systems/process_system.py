import abc
import csv
import json
import logging
import uuid
from typing import Dict, List, Type

from core.models.process import DataProcess, DataProcessEntity, EntityType, FileType, ProcessStatus
from core_logs.utils.error_helper import errors_to_str
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet

logger = logging.getLogger(__name__)


class FileLoader:
    @classmethod
    def load_csv_data(cls,
                      csv_file,
                      upload: uuid.UUID = None,
                      **kwargs):
        decoded_file = csv_file.read().decode('utf-8').splitlines()
        file_data = csv.DictReader(decoded_file, delimiter=',')
        process = cls._create_data_process(FileType.CSV, upload, **kwargs)
        entity_type = kwargs.get('entity_type')
        created_by_id = kwargs.get('created_by_id')

        match entity_type:
            case EntityType.COMPONENTS:
                status = ProcessStatus.PENDING
                error_message = ''
                components = []

                for line in file_data:
                    try:
                        permissions = []
                        if line['Permissions'] and line['Permissions'] != '':
                            for permission in line['Permissions'].split('|'):
                                model, app_label, codename = permission.split('.')
                                permissions.append({
                                    'codename': codename,
                                    'model': model,
                                    'app_label': app_label,
                                })
                        line['Permissions'] = permissions

                        children = []
                        if line['Children'] and line['Children'] != '':
                            for index, slug in enumerate(line['Children'].split('|')):
                                children.append({
                                    'slug': slug,
                                    'order': index
                                })
                        line['Children'] = children

                        line['Is Active'] = line['Is Active'].lower() == 'true'

                        if isinstance(line.get('Properties'), str):
                            props_str = line.get('Properties', '').strip()
                            if props_str:
                                try:
                                    line['Properties'] = json.loads(props_str)
                                except json.JSONDecodeError:
                                    try:
                                        props_str = props_str.replace("'", '"')
                                        props_str = props_str.replace('True', 'true')
                                        props_str = props_str.replace('False', 'false')
                                        if props_str.startswith('[') and props_str.endswith(']'):
                                            props_list = [s.strip().strip("'\"") for s in props_str[1:-1].split(',')]
                                            line['Properties'] = props_list
                                        else:
                                            line['Properties'] = json.loads(props_str)
                                    except Exception:
                                        line['Properties'] = {}
                            else:
                                line['Properties'] = {}

                        components.append(line)
                    except Exception as e:
                        logger.warning(f'Could not process child component or permissions: {line}', e)
                        error_message = errors_to_str(e)
                        status = ProcessStatus.FAILED
                        break

                DataProcessEntity(
                    process=process,
                    data=components,
                    created_by_id=created_by_id,
                    line_number=0,
                    status=status,
                    error_message=error_message
                ).save()
        return process

    @classmethod
    def load_tsv_data(cls,
                      tsv_file,
                      upload: uuid.UUID = None,
                      **kwargs):
        decoded_file = tsv_file.read().decode('utf-8').splitlines()
        file_data = csv.DictReader(decoded_file, delimiter='\t')
        process = cls._create_data_process(FileType.TSV, upload, **kwargs)
        entity_type = kwargs.get('entity_type')
        created_by_id = kwargs.get('created_by_id')

        match entity_type:
            case EntityType.PERMISSIONS:
                status = ProcessStatus.PENDING
                error_message = ''
                group_permissions = []
                try:
                    field_names = file_data.fieldnames
                    identifiers = [name for name in field_names[2:] if name]

                    permissions_dict = {
                        'orphan_permissions': []
                    }
                    for identifier in identifiers:
                        permissions_dict[identifier] = []

                    for line in file_data:
                        model, app_label, codename = line[field_names[0]].split('.')
                        _, permission_name = line[field_names[1]].split(':')
                        has_group = False

                        permission_data = {
                            'model': model,
                            'app_label': app_label,
                            'codename': codename,
                            'permission_name': permission_name
                        }
                        for identifier in identifiers:
                            if line[identifier].lower() == 'true':
                                has_group = True
                                permissions_dict[identifier].append(permission_data)

                        if not has_group:
                            permissions_dict['orphan_permissions'].append(permission_data)

                    for identifier, permissions in permissions_dict.items():
                        if identifier == 'orphan_permissions':
                            group_permissions.append({
                                'permissions': permissions
                            })
                        else:
                            organization, group = identifier.split('|')
                            group_permissions.append({
                                'organization': organization,
                                'group': group,
                                'permissions': permissions
                            })
                except Exception as e:
                    logger.exception('Could not process permissions data', e)
                    error_message = errors_to_str(e)
                    status = ProcessStatus.FAILED
                    process.update_status(status, error_message)

                DataProcessEntity(
                    process=process,
                    data=group_permissions,
                    created_by_id=created_by_id,
                    line_number=0,
                    status=status,
                    error_message=error_message
                ).save()

            case _:
                row_num = 2
                for line in file_data:
                    try:
                        with transaction.atomic():
                            DataProcessEntity(process=process,
                                              data=line,
                                              created_by_id=created_by_id,
                                              line_number=row_num).save()
                    except Exception as e:
                        logger.exception(f'Could not import data from row: {row_num}', e)
                    finally:
                        row_num += 1
        return process

    @classmethod
    def create_entity_from_dict(cls, file_data: Dict,
                                process: DataProcess,
                                language_code: int,
                                created_by_id: int = None,
                                prefix: str = ''):
        for key, value in file_data.items():
            field_path = f'{prefix}.{key}' if prefix else key
            if isinstance(value, Dict):
                cls.create_entity_from_dict(value, process, language_code, created_by_id, field_path)
            else:
                try:
                    with transaction.atomic():
                        data = {'key': field_path, 'text': value, 'language_code': language_code}
                        DataProcessEntity(process=process, data=data, created_by_id=created_by_id,
                                          line_number=0).save()
                except Exception as e:
                    logger.exception(f'Could not import data with key: {prefix}.{key}', e)

    @classmethod
    def create_entity_from_list_dict(cls, file_data: List[Dict],
                                     process: DataProcess,
                                     created_by_id: int = None):
        try:
            with transaction.atomic():
                for line in file_data:
                    DataProcessEntity(process=process, data=line, created_by_id=created_by_id, line_number=0).save()
        except Exception as e:
            logger.exception('Could not import data from json list', e)
            process.update_status(ProcessStatus.FAILED, errors_to_str(e))

    @classmethod
    def load_json_data(cls,
                       json_file,
                       upload: uuid.UUID = None,
                       **kwargs):

        file_data = json.loads(json_file.read().decode('utf-8'))
        if 'file_type' in kwargs:
            del kwargs['file_type']
        process = cls._create_data_process(FileType.JSON, upload, **kwargs)

        language_code = kwargs.get('language_code', None)
        cls.create_entity_from_dict(file_data, process, language_code, kwargs.get('created_by_id', None))
        return process

    @classmethod
    def load_api_data(cls, **kwargs):
        file_name = kwargs.pop('file_name', '') + ' loaded via API endpoint'
        process = cls._create_data_process(FileType.API, None, file_name=file_name, **kwargs)
        entity_processor: EntityProcessor = EntityProcessor.get_processor(process)

        api_json_data = entity_processor.load_api_data(process)

        if api_json_data is None and process.status == ProcessStatus.PENDING:
            process.update_status(ProcessStatus.FAILED, 'API request not implemented')
            return process

        created_by_id = kwargs.get('created_by_id', None)
        cls.create_entity_from_list_dict(api_json_data, process, created_by_id)
        return process

    @classmethod
    def load_data(cls, file, file_format, upload=None, **kwargs):
        match file_format:
            case FileType.TSV:
                return cls.load_tsv_data(file, upload, **kwargs)
            case FileType.CSV:
                return cls.load_csv_data(file, upload, **kwargs)
            case FileType.JSON:
                return cls.load_json_data(file, upload, **kwargs)
            case FileType.API:
                return cls.load_api_data(**kwargs)

        raise Exception(f'Requested file format {file_format} not implemented')

    @classmethod
    def _create_data_process(cls, file_type, upload, **kwargs):
        return DataProcess.objects.create(
            created_by_id=kwargs.get('created_by_id', None),
            entity_type=kwargs.get('entity_type', None),
            file_name=kwargs.get('file_name', None),
            file_type=file_type,
            status=ProcessStatus.PENDING,
            updated_by_id=kwargs.get('created_by_id', None),
            uploaded_file_id=upload,
        )


class EntityProcessor(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def process(cls, records, user_id: Type[int], overwrite: bool = False) -> ProcessStatus:
        ...

    @classmethod
    @abc.abstractmethod
    def load_api_data(cls, process) -> List[Dict]:
        ...

    @classmethod
    def get_processor(cls, process: DataProcess):
        """
        Get processor for an entity type from the registry.

        Domain apps register their processors in apps.py ready() method.
        This allows core to remain generic and domain-agnostic.
        """
        from core.utils.processor_registry import get_processor

        processor_class = get_processor(process.entity_type)

        if processor_class is None:
            raise Exception(
                f'No processor registered for entity type {process.entity_type}. '
                f'Domain apps must register processors in apps.py ready() method.'
            )

        return processor_class


class ProcessSystem(abc.ABC):
    mimetypes = dict((v, k) for k, v in FileType.choices)

    @classmethod
    @abc.abstractmethod
    def load_data(cls,
                  request_obj,
                  upload: uuid.UUID = None,
                  **kwargs):
        ...

    @classmethod
    def change_status(cls, records: QuerySet[DataProcess],
                      status: ProcessStatus,
                      description: str = 'Status reset to pending'):
        for record in records:
            record.update_status(status, description)

        DataProcess.objects.bulk_update(records, ['status', 'status_date', 'status_description'])

    @classmethod
    def process(cls, process: DataProcess, user: User, overwrite: bool):
        try:
            process.update_status(ProcessStatus.PROCESSING)
            logger.info(f"Started processing DataProcessEntities for batch {process.batch}")
            DataProcessEntity.objects.filter(status__in=[ProcessStatus.PENDING, ProcessStatus.FAILED],
                                             process=process
                                             ).update(status=ProcessStatus.PROCESSING)
            data_rows = DataProcessEntity.objects.filter(process=process,
                                                         status__exact=ProcessStatus.PROCESSING
                                                         ).order_by('id')[:25]
            resulting_status = ProcessStatus.DONE
            entity_processor: EntityProcessor = EntityProcessor.get_processor(process)

            if overwrite and not (
                    hasattr(entity_processor, 'allows_overwrite') and entity_processor.allows_overwrite is True):
                process.update_status(ProcessStatus.FAILED, "Overwrite action not supported by this model")
                return process

            while data_rows.count() > 0:
                if entity_processor.process(data_rows, process.created_by_id, overwrite) == ProcessStatus.FAILED:
                    resulting_status = ProcessStatus.FAILED
                data_rows = DataProcessEntity.objects.filter(process=process,
                                                             status__exact=ProcessStatus.PROCESSING).order_by('id')[:25]
        except Exception as e:
            logger.exception(f'Failed to process batch: {process.batch}', e)
            resulting_status = ProcessStatus.FAILED
        process.update_status(resulting_status)
        logger.info(f"Finished processing DataProcessEntities for batch {process.batch}")
        return process


class AdminProcessSystem(ProcessSystem):

    @classmethod
    def load_data(cls,
                  request_obj,
                  upload: uuid.UUID = None,
                  **kwargs):
        entity_type = request_obj.POST['entity_type'] if 'entity_type' in request_obj.POST else kwargs.get('entity_type')
        file_type = FileType.mimetype(
            request_obj.POST['file_type'] if 'file_type' in request_obj.POST else request_obj.FILES[
                'data_file'].content_type)
        return FileLoader.load_data(request_obj.FILES.get('data_file', None),
                                    file_type,
                                    upload,
                                    **kwargs | {
                                        'entity_type': entity_type,
                                        'language_code': request_obj.POST['language_code']
                                    })


class AwsProcessSystem(ProcessSystem):

    @classmethod
    def load_data(cls,
                  request_obj,
                  upload: uuid.UUID = None,
                  **kwargs):
        file_type = cls.mimetypes[request_obj['ContentType']]
        return FileLoader.load_data(request_obj['Body'], file_type, upload, **kwargs)


class LocalFileProcessSystem(ProcessSystem):

    @classmethod
    def load_data(cls,
                  request_obj,
                  upload: uuid.UUID = None,
                  **kwargs):
        return FileLoader.load_data(request_obj, kwargs.get('file_type'), None, **kwargs)


class InternalProcessSystem(ProcessSystem):

    @classmethod
    def load_data(cls,
                  request_obj=None,
                  upload: uuid.UUID = None,
                  **kwargs):
        file_type = kwargs.pop('file_type')
        return FileLoader.load_data(
            request_obj,
            file_type,
            upload,
            **kwargs
        )

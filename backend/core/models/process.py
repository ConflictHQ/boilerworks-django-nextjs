import uuid

from core.models import Tracking, Upload
from django.db import models
from django.utils import timezone


class ProcessStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    PROCESSING = 'PROCESSING', 'Processing'
    IGNORED = 'IGNORED', 'Ignored'
    DONE = 'DONE', 'Done'
    FAILED = 'FAILED', 'Failed'


class FileType(models.TextChoices):
    CSV = 'CSV', 'text/csv'
    TSV = 'TSV', 'text/tab-separated-values'
    JSON = 'JSON', 'application/json'
    API = 'API', 'api/endpoint'

    @classmethod
    def mimetype(cls, label):
        if label in cls.__members__:
            return cls.__members__[label]
        key = next((key for key, value in cls.__members__.items() if value.label == label), None)
        return key


class EntityType(models.TextChoices):
    EMPLOYEE = 'EMPLOYEE', 'Employee'
    FIELDFLO = 'FIELDFLO', 'FieldFlo'
    SITE_LABEL = 'SITE_LABEL', 'Site label'
    PERMISSIONS = 'PERMISSIONS', 'Permissions'
    COMPONENTS = 'COMPONENTS', 'Components'


MAX_DESCRIPTION_LENGTH = 1024


class DataProcess(Tracking):
    class Meta:
        indexes = [models.Index(fields=['status'])]
        verbose_name_plural = 'Data Processes'

    batch = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    file_name = models.CharField(max_length=130, null=True, blank=True)
    file_type = models.CharField(max_length=10, choices=FileType.choices, blank=False, null=False)
    entity_type = models.CharField(max_length=50, choices=EntityType.choices, blank=False, null=False)

    gid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    status = models.CharField(max_length=10, choices=ProcessStatus.choices, default=ProcessStatus.PENDING)
    status_date = models.DateTimeField(null=True, blank=True, editable=False,
                                       help_text='Date when the status was updated')
    status_description = models.CharField(max_length=MAX_DESCRIPTION_LENGTH, null=True, blank=True, editable=False)
    uploaded_file = models.ForeignKey(Upload, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f'{self.batch} - {self.status}'

    def update_status(self, status: ProcessStatus, description: str = None):
        self.status = status
        self.status_date = timezone.now()
        self.status_description = description[:MAX_DESCRIPTION_LENGTH] if description else None
        self.save()


class DataProcessEntity(Tracking):
    class Meta:
        verbose_name_plural = 'Data Processes Entities'
    data = models.JSONField(default=dict, blank=True, null=True, help_text='Row data')
    line_number = models.IntegerField(help_text='Line number in uploaded file.', null=False)
    error_message = models.TextField(null=True, blank=True)
    process = models.ForeignKey(DataProcess, related_name="rows", null=True, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=ProcessStatus.choices, default=ProcessStatus.PENDING)
    status_date = models.DateTimeField(null=True, blank=True, editable=False,
                                       help_text='Date when the status was updated')

    def update_status(self, status: ProcessStatus, error_message: str = None):
        self.error_message = error_message
        self.status = status
        self.status_date = timezone.now()
        self.save()

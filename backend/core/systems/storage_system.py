import hashlib

from core.models import ResourceFile
from django.conf import settings
from google.cloud import storage


class StorageSystem:
    _storage_client_instance = None

    @classmethod
    def storage_client(cls):
        if cls._storage_client_instance:
            return cls._storage_client_instance

        cls._storage_client_instance = storage.Client\
            .from_service_account_json(settings.GOOGLE_APPLICATION_CREDENTIALS)

        return cls._storage_client_instance

    @classmethod
    def create_upload_link(cls, name, content_type):
        bucket = cls.storage_client().get_bucket(settings.GS_BUCKET_NAME)
        blob = bucket.blob(name)
        url = blob.generate_signed_url(
            version='v4',
            expiration=3600,
            method='POST',
            content_type=content_type,
            # headers={
            #     'x-goog-test': 'value'
            # },
        )

        return url

    @classmethod
    def save_file(cls, user, module, gid, file, public=False):
        access = 'public-read' if public else 'private'
        name = f'{access}/{module}/{gid}/{file.name}'
        gid = hashlib.md5(name.encode()).hexdigest()
        rf, created = ResourceFile.objects.get_or_create(
            gid=gid,
            is_public=public,
        )

        if created:
            rf.created_by = user
            rf.name = file.name
            rf.save()

        rf.file.save(name, file)
        if public:
            rf.file.storage.bucket.blob(rf.file.name).make_public()
        return rf

    @classmethod
    def get_url(cls, rf: ResourceFile):
        blob = rf.file.storage.bucket.blob(rf.file.name)
        if rf.is_public:
            return blob.public_url

        return blob.generate_signed_url(
            version='v4',
            expiration=3600,
            method='GET',
        )

from typing import List, Optional

import graphene
from config.roles_gen import P
from core.models import Profile, Upload
from core.schema.upload import UploadType
from graphql_relay import from_global_id

# Optional import - Domain-specific functionality
try:
    from domain_app.models import ApprovalRequest
    HAS_DOMAIN_APP = True
except ImportError:
    ApprovalRequest = None
    HAS_DOMAIN_APP = False

from .upload import PreSignedUrlImageUploadMutation

ProfileImageField = graphene.Enum.from_enum(Profile.ImageField)


class ProfileImageFieldUploadMutation(graphene.Mutation):
    class Arguments:

        global_id = graphene.ID(
            required=True,
            description='Global id of the profile to be updated',
        )

        mimetype = graphene.String(
            required=True,
            description='Content Type of the object to be uploaded.',
        )

        metadata = graphene.JSONString(
            required=False,
            description='Additional metadata about the file uploaded.',
        )

        field = graphene.Argument(
            ProfileImageField,
            description='Image field to be uploaded',
        )

    upload = graphene.Field(UploadType)

    @classmethod
    def mutate(
            cls,
            _root,
            info,
            global_id: str,
            mimetype: str,
            field: Optional[Profile.ImageField] = None,
            metadata: Optional[dict] = None,
            **kwargs):

        model_name, pk = from_global_id(global_id)
        assert model_name != Profile._meta.model_name
        profile_original: Profile = Profile.objects.get(pk=pk)
        whitelist: List[str] = Profile.whitelist_fields()

        if field.value in whitelist:
            # Skip approval request flow
            return ProfileImageFieldUploadMutation(
                upload=cls.save_upload(field, global_id, info, metadata, mimetype, profile_original)
            )

        original, draft = Profile.objects.get_draft(profile_original)

        # Use approval request if domain app is available
        if HAS_DOMAIN_APP:
            with ApprovalRequest.objects.for_instance(
                    instance=draft,
                    permission=P.PROFILE_APPROVE_CHANGES.perm(),
                    created_by=info.context.user
            ):
                profile = draft
                profile.document_option = Profile.DocumentOptions.DRAFTED

                upload = cls.save_upload(field, global_id, info, metadata, mimetype, profile)
        else:
            # Without domain app, directly update the profile
            profile = draft
            upload = cls.save_upload(field, global_id, info, metadata, mimetype, profile)

        return ProfileImageFieldUploadMutation(upload=upload)

    @classmethod
    def save_upload(cls, field, global_id, info, metadata, mimetype, profile):
        upload: Optional[Upload] = None
        match field:
            case Profile.ImageField.AVATAR:
                upload = profile.avatar
            case Profile.ImageField.SIGNATURE:
                upload = profile.signature
        if upload and upload.content_type != mimetype:
            # We can recycle the upload if it has the same mime type
            upload = None
        upload = PreSignedUrlImageUploadMutation.create_upload(
            info=info,
            global_id=global_id,
            mimetype=mimetype,
            location=Upload.Location.PUBLIC,
            metadata=metadata,
            upload=upload,
        )
        match field:
            case Profile.ImageField.AVATAR:
                profile.avatar = upload
                if profile.user_id:
                    profile.draft.avatar = upload
            case Profile.ImageField.SIGNATURE:
                profile.signature = upload
                if profile.user_id:
                    profile.draft.signature = upload
        profile.save()
        if profile.user_id:
            profile.draft.save()
        return upload

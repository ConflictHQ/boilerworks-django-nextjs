from graphene_django.debug import DjangoDebug

from .address import *  # noqa
from .common import *  # noqa
from .enums import *  # noqa
from .library import LibraryQuery  # noqa: F403
from .localization import SiteLabelQuery
from .metabase import *  # noqa
from .metabase_unimported_chart import *  # noqa
from .mutations import *  # noqa
from .notification import *  # noqa
from .permissions import *  # noqa
from .process import ProcessQuery
from .user import *  # noqa


class Mutation(graphene.ObjectType):
    upsert_user = UpsertUserMutation.Field()
    profile = ProfileMutation.Field()
    profile_image_field_upload = ProfileImageFieldUploadMutation.Field()
    profile_request_pwd_change = RequestPwdChangeMutation.Field()
    profile_request_delete_user = RequestDeleteUserMutation.Field()

    delete = DeleteMutation.Field()
    activate = ActivateMutation.Field()

    switch_user = SwitchUserMutation.Field()
    pin_update = PinUpdateMutation.Field()

    pre_signed_url_image_upload = PreSignedUrlImageUploadMutation.Field()
    confirm_pre_signed_url_image_upload = ConfirmPreSignedUrlImageUploadMutation.Field()
    upload_text_file = DataImportFileUploadMutation.Field()
    process_file = ProcessFileMutation.Field()
    file_upload = FileUploadMutation.Field(deprecation_reason="Folding functionality into pre_signed_url_image_upload.")

    login = LoginMutation.Field()
    logout = LogoutMutation.Field()

    debug = graphene.Field(DjangoDebug, name="_core_debug")
    metabase_chart = MetabaseChartMutation.Field()
    notification = NotificationMutation.Field()
    notification_read = NotificationReadMutation.Field()
    permission_group_operation = GroupOperationMutation.Field()

    library_mkdir = LibraryMkdirMutation.Field()
    library_rmdir = LibraryRmdirMutation.Field()
    library_rename_dir = LibraryRenameDirectoryMutation.Field()
    library_rename_file = LibraryRenameFileMutation.Field()
    library_rm_file = LibraryRmFileMutation.Field()
    library_set_icon = LibrarySetIconMutation.Field()

    generate_rocket_chat_token = GenerateRocketChatTokenMutation.Field()


class Query(
    PermissionsQuery,
    UserQuery,
    NotificationQuery,
    ProcessQuery,
    SiteLabelQuery,
    LibraryQuery,
    MetabaseChartQuery,
    MetabaseUnimportedChartQuery,
    graphene.ObjectType
):
    address = graphene.Field(AddressType, id=graphene.String())
    debug = graphene.Field(DjangoDebug, name="_core_debug")

    @staticmethod
    def resolve_address(root, info, id, **kwargs):
        return AddressType.get_object(info, id)


schema = graphene.Schema(query=Query, mutation=Mutation)


class CoreAuthMutation(graphene.ObjectType):
    login = LoginMutation.Field()


class CoreAuthQuery(graphene.ObjectType):
    debug = graphene.Field(DjangoDebug, name="_core_debug")


# This schema is used for authentications between the client and the server.
# It is not secure and should not be used for any other purpose.
schema_auth = graphene.Schema(query=CoreAuthQuery, mutation=CoreAuthMutation)

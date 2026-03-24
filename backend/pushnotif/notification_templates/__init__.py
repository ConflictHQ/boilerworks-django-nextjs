from dataclasses import dataclass

from core.models import SignRequest
from core.utils.resources import EmbeddedResource
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from pushnotif.service import BaseNotification, NotificationDefinition, NotificationParameters


@dataclass
class NewUserBroadcastParameters(NotificationParameters):

    new_user: User
    creator: User
    broadcast_recipient: User

    @cached_property
    def receiver(self) -> str:
        return f'{self.new_user.first_name} {self.new_user.last_name}'

    @cached_property
    def sender(self) -> str:
        return f'{self.creator.first_name} {self.creator.last_name}'

    @cached_property
    def recipient(self) -> str:
        # Broadcast recipient must be assigned dynamically
        return f'{self.broadcast_recipient.first_name} {self.broadcast_recipient.last_name}'


@dataclass
class SignRequestParameters(NotificationParameters):
    sign_request: SignRequest
    recipient: str

    @cached_property
    def sender(self) -> str:
        user = self.sign_request.user
        return f'{user.first_name} {user.last_name}'


class NotificationResources(EmbeddedResource):
    # Evaluations
    EVALUATIONS_RECEIVED_BROADCAST_EMAIL_BODY_HTML = 'user_management_example/new_user_broadcast/email.body.html'
    EVALUATIONS_RECEIVED_BROADCAST_EMAIL_HEADER_HTML = 'user_management_example/new_user_broadcast/email.header.html'
    EVALUATIONS_RECEIVED_BROADCAST_SMS_BODY_TXT = 'user_management_example/new_user_broadcast/sms.body.txt'
    EVALUATIONS_RECEIVED_BROADCAST_SMS_HEADER_TXT = 'user_management_example/new_user_broadcast/sms.header.txt'
    EVALUATIONS_RECEIVED_BROADCAST_IOS_BODY_TXT = 'user_management_example/new_user_broadcast/ios.body.txt'
    EVALUATIONS_RECEIVED_BROADCAST_IOS_HEADER_TXT = 'user_management_example/new_user_broadcast/ios.header.txt'
    EVALUATIONS_RECEIVED_BROADCAST_ANDROID_BODY_TXT = 'user_management_example/new_user_broadcast/android.body.txt'
    EVALUATIONS_RECEIVED_BROADCAST_ANDROID_HEADER_TXT = 'user_management_example/new_user_broadcast/android.header.txt'
    EVALUATIONS_RECEIVED_BROADCAST_WEBAPP_BODY_HTML = 'user_management_example/new_user_broadcast/webapp.body.html'
    EVALUATIONS_RECEIVED_BROADCAST_WEBAPP_HEADER_HTML = 'user_management_example/new_user_broadcast/webapp.header.html'

    # Signatures
    SIGNATURES_REQUESTED_EMAIL_BODY_HTML = 'signatures/requested/email.body.html'
    SIGNATURES_REQUESTED_EMAIL_HEADER_HTML = 'signatures/requested/email.header.html'
    SIGNATURES_REQUESTED_SMS_BODY_TXT = 'signatures/requested/sms.body.txt'
    SIGNATURES_REQUESTED_SMS_HEADER_TXT = 'signatures/requested/sms.header.txt'
    SIGNATURES_REQUESTED_IOS_BODY_TXT = 'signatures/requested/ios.body.txt'
    SIGNATURES_REQUESTED_IOS_HEADER_TXT = 'signatures/requested/ios.header.txt'
    SIGNATURES_REQUESTED_ANDROID_BODY_TXT = 'signatures/requested/android.body.txt'
    SIGNATURES_REQUESTED_ANDROID_HEADER_TXT = 'signatures/requested/android.header.txt'
    SIGNATURES_REQUESTED_WEBAPP_BODY_HTML = 'signatures/requested/webapp.body.html'
    SIGNATURES_REQUESTED_WEBAPP_HEADER_HTML = 'signatures/requested/webapp.header.html'


class Notifications(BaseNotification):

    NEW_USER_BROADCAST: BaseNotification = NotificationDefinition(
        identifier="user_management_example/new_user_broadcast",
        schema=NewUserBroadcastParameters,
        email_header_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_EMAIL_HEADER_HTML,
        email_body_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_EMAIL_BODY_HTML,
        android_push_header_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_ANDROID_HEADER_TXT,
        android_push_body_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_ANDROID_BODY_TXT,
        ios_push_header_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_IOS_HEADER_TXT,
        ios_push_body_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_IOS_BODY_TXT,
        webapp_header_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_WEBAPP_HEADER_HTML,
        webapp_body_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_WEBAPP_BODY_HTML,
        sms_header_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_SMS_HEADER_TXT,
        sms_body_template=NotificationResources.EVALUATIONS_RECEIVED_BROADCAST_SMS_BODY_TXT,
    )

    SIGNATURES_REQUESTED = NotificationDefinition(
        identifier='signatures/requested',
        schema=SignRequestParameters,
        email_header_template=NotificationResources.SIGNATURES_REQUESTED_EMAIL_HEADER_HTML,
        email_body_template=NotificationResources.SIGNATURES_REQUESTED_EMAIL_BODY_HTML,
        android_push_header_template=NotificationResources.SIGNATURES_REQUESTED_ANDROID_HEADER_TXT,
        android_push_body_template=NotificationResources.SIGNATURES_REQUESTED_ANDROID_BODY_TXT,
        ios_push_header_template=NotificationResources.SIGNATURES_REQUESTED_IOS_HEADER_TXT,
        ios_push_body_template=NotificationResources.SIGNATURES_REQUESTED_IOS_BODY_TXT,
        webapp_header_template=NotificationResources.SIGNATURES_REQUESTED_WEBAPP_HEADER_HTML,
        webapp_body_template=NotificationResources.SIGNATURES_REQUESTED_WEBAPP_BODY_HTML,
        sms_header_template=NotificationResources.SIGNATURES_REQUESTED_SMS_HEADER_TXT,
        sms_body_template=NotificationResources.SIGNATURES_REQUESTED_SMS_BODY_TXT,
    )

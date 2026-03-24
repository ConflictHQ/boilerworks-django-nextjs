import enum
from email.headerregistry import Address as EmailAddress

import pydash
from constance import config
from core.models import TemplateModel, Tracking
from core.models.common import GlobalIDLink
from core.models.dfa import DfaInstance, state
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django_celery_beat.models import CrontabSchedule
from firebase_admin import messaging
from pushnotif.models.delivery_method import DeliveryMethods
from pushnotif.twilio import TwilioService

from .category import DeliveryMethod, NotificationCategories, NotificationCategory
from .device import DeviceToken


class SentStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    SENT = 'SENT', 'Sent'
    FAILED = 'FAILED', 'Failed'


class Result(enum.Enum):
    SUCCESS = "success"
    RETRY = "retry"
    ABORT = "abort"

    @classmethod
    def _missing_(cls, value):
        match value:
            case StopIteration():
                return cls.RETRY
            case _:
                return cls.ABORT


class PushNotification(DfaInstance):
    title = models.CharField(max_length=256)

    message = models.CharField(max_length=4096, blank=True)

    data = models.JSONField(null=True, blank=True, default=dict)

    response = models.TextField(blank=True, default='')

    sent_at = models.DateTimeField(null=True, blank=True)

    acknowledge_at = models.DateTimeField(null=True, blank=True)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    category = models.ForeignKey(
        NotificationCategory,
        on_delete=models.CASCADE,
        default=NotificationCategories.default_notification_category,
        null=True,
        blank=True,
    )

    delivery_method = models.ForeignKey(to=DeliveryMethod, on_delete=models.CASCADE, null=True)

    @state(
        is_initial=True,
        scheduler_options={},
        crontab=CrontabSchedule(minute='*'),
    )
    def on_requested(self) -> Result:
        if self.device_tokens:
            return Result.SUCCESS
        return Result.ABORT

    @state(crontab=CrontabSchedule(minute='*'))
    def on_sending(self) -> Result:

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=self.title,
                body=self.message
            ),
            tokens=self.device_tokens
        )

        if self.data is not None and len(self.data):
            message.data = self.data

        from pushnotif.firebase import Firebase

        firebase = Firebase()
        batch_responses = firebase.send(message)
        response_text = f'Success count:{batch_responses.success_count} Failure count:{batch_responses.failure_count}\n'

        for response in batch_responses.responses:
            exception_message = str(response.exception) + "\n"
            response_text += exception_message

        self.response = response_text
        self.sent_at = timezone.now()

        return Result.SUCCESS

    @state(is_final=True)
    def on_skipped(self) -> Result:
        return Result.ABORT

    @state(is_final=True)
    def on_sent(self) -> Result:
        return Result.ABORT

    @state(is_final=True)
    def on_failed(self) -> Result:
        return Result.ABORT

    transitions = {
        on_requested: {
            Result.SUCCESS: on_sending,
            Result.RETRY: on_requested,
            Result.ABORT: on_skipped,
        },
        on_sending: {
            Result.SUCCESS: on_sent,
            Result.RETRY: on_sending,
            Result.ABORT: on_failed,
        },
    }

    @cached_property
    def device_tokens(self) -> list[str]:
        queryset = DeviceToken.objects.filter(recipient_id=self.recipient_id, delivery_method=self.delivery_method)
        return list(queryset.values_list("device_token", flat=True))

    def send(self) -> SentStatus:
        self.state = self.initial_state
        self.save()
        return SentStatus.PENDING

    @property
    def global_id(self):
        from graphene_django.registry import get_global_registry

        registry = get_global_registry()
        return registry.get_type_for_model(type(self)).to_global_id(self)


class SMSNotification(Tracking):
    title = models.CharField(max_length=256)

    message = models.CharField(max_length=4096, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)

    sid = models.TextField(null=True, blank=True)

    response = models.TextField(null=True, blank=True)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def send(self) -> SentStatus:
        twilio_service = TwilioService()
        message = twilio_service.send_sms(
            to_number=self.recipient.profile.phone_number.raw_input,
            message=self.message
        )
        self.sid = message.sid
        self.save()
        return SentStatus.PENDING

    def update_status(self, status: str):
        self.response = status

        sent_status = None
        match status:
            case 'sent' | 'delivered' | 'received' | 'accepted' | 'read':
                sent_status = SentStatus.SENT
                self.sent_at = timezone.now()
            case 'failed' | 'undelivered' | 'canceled':
                sent_status = SentStatus.FAILED
            case 'queued' | 'sending' | 'receiving' | 'scheduled':
                sent_status = SentStatus.PENDING

        if sent_status is not None:
            gid = GlobalIDLink.objects.filter(gid=self.global_id).values_list('id', flat=True).first()
            NotificationEventMethod.objects.filter(related_gid=gid).first().update_status(status=sent_status)


class EmailNotification(Tracking):
    title = models.CharField(max_length=256)

    message = models.CharField(max_length=4096, blank=True)

    sent_at = models.DateTimeField(null=True, blank=True)

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    def send(self) -> SentStatus:
        email = EmailMessage(
            subject=self.title,
            body=self.message,
            from_email=str(EmailAddress(addr_spec=settings.FROM_EMAIL)),
            to=[str(EmailAddress(
                display_name=f"{self.recipient.first_name} {self.recipient.last_name}",
                addr_spec=self.recipient.email
                ))],
            cc=[],
            bcc=[],
        )
        email.content_subtype = "html"
        response = email.send()
        self.sent_at = timezone.now()
        self.save()
        if response == 0:
            return SentStatus.FAILED
        return SentStatus.SENT


class NotificationTemplate(Tracking):
    name = models.CharField(max_length=64, primary_key=True)

    display_name = models.CharField(max_length=64)

    app_label = models.CharField(max_length=128, null=True, blank=False)

    classname = models.CharField(max_length=1024, null=True, blank=False)

    member = models.CharField(max_length=128, null=True, blank=False)

    parameters = models.CharField(max_length=1024, null=True, blank=False)

    delivery_method_templates = models.ManyToManyField(DeliveryMethod, through='DeliveryMethodNotificationTemplate')

    def __str__(self):
        return pydash.human_case(self.name)


class DeliveryMethodNotificationTemplate(Tracking):
    notification_template = models.ForeignKey(to=NotificationTemplate, on_delete=models.CASCADE)

    delivery_method = models.ForeignKey(to=DeliveryMethod, on_delete=models.CASCADE)

    always_send_notification = models.BooleanField(default=False)

    never_send_notification = models.BooleanField(default=False)

    header_template = models.ForeignKey(
        TemplateModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+')

    body_template = models.ForeignKey(
        TemplateModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+')


class NotificationEvent(Tracking):
    """
    Records all notifications sent through the system, regardless of delivery method.
    """
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_notifications',
    )

    status = models.CharField(
        max_length=32,
        choices=SentStatus.choices,
        default=SentStatus.PENDING,
    )
    status_date = models.DateTimeField(null=True, blank=True, editable=False, help_text='Date when the status was updated')
    error_message = models.TextField(blank=True, null=True)

    def send(self):
        for notification_event_method in NotificationEventMethod.objects.filter(notification_event=self):
            notification_event_method.send()

    def refresh_status(self):
        statuses = NotificationEventMethod.objects.filter(notification_event=self).values_list("status", flat=True)
        if SentStatus.FAILED in statuses:
            self.update_status(status=SentStatus.FAILED)
        elif SentStatus.PENDING in statuses:
            self.update_status(status=SentStatus.PENDING)
        elif all(status == SentStatus.SENT for status in statuses):
            self.update_status(status=SentStatus.SENT)

    def update_status(self, status: SentStatus, error_message: str = None):
        self.error_message = error_message
        self.status = status
        self.status_date = timezone.now()
        self.save()


class NotificationEventMethod(Tracking):
    related_gid = models.ForeignKey(GlobalIDLink, on_delete=models.CASCADE)

    delivery_method = models.ForeignKey(DeliveryMethod, on_delete=models.CASCADE)

    notification_event = models.ForeignKey(NotificationEvent, on_delete=models.CASCADE)

    status = models.CharField(max_length=32, choices=SentStatus.choices, default=SentStatus.PENDING)

    status_date = models.DateTimeField(null=True, blank=True, editable=False, help_text='Date when the status was updated')

    error_message = models.TextField(blank=True, null=True)

    def send(self):
        notification = self.related_gid
        delivery_method = self.delivery_method
        try:
            match (delivery_method.enum, notification.type_name):
                case (DeliveryMethods.ANDROID | DeliveryMethods.IOS, "PushNotificationType"):
                    if config.PUSH_NOTIFICATIONS:
                        status = notification.get_instance().send()
                        self.update_status(status=status)
                case (DeliveryMethods.SMS, 'SMSNotificationType'):
                    if config.SMS_NOTIFICATIONS:
                        status = notification.get_instance().send()
                        self.update_status(status=status)
                case (DeliveryMethods.EMAIL, "EmailNotificationType"):
                    if config.EMAIL_NOTIFICATIONS:
                        status = notification.get_instance().send()
                        self.update_status(status=status)
                case (DeliveryMethods.WEBAPP, "NotificationType"):
                    if config.WEBAPP_NOTIFICATIONS:
                        if notification.get_instance() is None:
                            self.update_status(
                                status=SentStatus.FAILED,
                                error_message=f"Not supported notification type {notification.type_name}"
                            )
                        else:
                            self.update_status(status=SentStatus.SENT)
                case _:
                    self.update_status(status=SentStatus.FAILED, error_message=f"Not supported notification type {notification.type_name}")
        except Exception as e:
            self.update_status(status=SentStatus.FAILED, error_message=f"Error sending notification: {e}")
            raise e

    def update_status(self, status: SentStatus, error_message: str = None):
        self.error_message = error_message
        self.status = status
        self.status_date = timezone.now()
        self.save()
        self.notification_event.refresh_status()

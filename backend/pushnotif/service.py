import abc
import enum
import logging
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import pydash
from core.models import GlobalIDLink, Notification, TemplateModel
from core.utils.resources import EmbeddedResource
from core_logs.utils.error_helper import errors_to_str
from django.conf import settings
from django.db import DatabaseError
from django.db.models import Model
from django.template import Context, Template
from django.template.engine import Engine
from django.utils.safestring import SafeString

from .models import DeliveryMethod, DeliveryMethods, DeviceToken
from .models.deep_link import DeepLink
from .models.notification import (
    DeliveryMethodNotificationTemplate,
    EmailNotification,
    NotificationEvent,
    NotificationEventMethod,
    NotificationTemplate,
    PushNotification,
    SentStatus,
    SMSNotification,
)
from .utils.notification_config_validator import NotificationConfigValidator

logger = logging.getLogger(__name__)


@dataclass
class NotificationDefinition:
    """
    Email definition class
    """

    """
    Unique identifier in the system
    """
    identifier: str

    """
    Body Template
    """
    schema: type

    """
    Email Default Subject
    """
    email_header_template: Optional[EmbeddedResource] = None

    """
    Email Template Location
    """
    email_body_template: Optional[EmbeddedResource] = None

    """
    Android Push Default Subject
    """
    android_push_header_template: Optional[EmbeddedResource] = None

    """
    Push Template Location
    """
    android_push_body_template: Optional[EmbeddedResource] = None

    """
    IOS Push Default Subject
    """
    ios_push_header_template: Optional[EmbeddedResource] = None

    """
    IOS Push Template Location
    """
    ios_push_body_template: Optional[EmbeddedResource] = None

    """
    Push Default Subject
    """
    webapp_header_template: Optional[EmbeddedResource] = None

    """
    Web Template Location
    """
    webapp_body_template: Optional[EmbeddedResource] = None

    """
    Push Default Subject
    """
    sms_header_template: Optional[EmbeddedResource] = None

    """
    Web Template Location
    """
    sms_body_template: Optional[EmbeddedResource] = None

    def delivery_method_templates(self) -> Iterable[Tuple[DeliveryMethods, EmbeddedResource, EmbeddedResource]]:
        if self.email_header_template and self.email_body_template:
            yield DeliveryMethods.EMAIL, self.email_header_template, self.email_body_template
        if self.android_push_header_template and self.android_push_body_template:
            yield DeliveryMethods.ANDROID, self.android_push_header_template, self.android_push_body_template
        if self.ios_push_header_template and self.ios_push_body_template:
            yield DeliveryMethods.IOS, self.ios_push_header_template, self.ios_push_body_template
        if self.webapp_header_template and self.webapp_body_template:
            yield DeliveryMethods.WEBAPP, self.webapp_header_template, self.webapp_body_template
        if self.sms_header_template and self.sms_body_template:
            yield DeliveryMethods.SMS, self.sms_header_template, self.sms_body_template


class NotificationParameters(abc.ABC):
    """
    Base class for email Body Compatible for Django Template Context(s)
    """

    def __getitem__(self, item):
        return getattr(self, item)

    def __contains__(self, item):
        return hasattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)


class BaseNotification(enum.Enum):
    """
    Provides support for listing existing notifications inside an application.
    """

    _notifications: dict[str, "BaseNotification"]

    def __init__(self, definition: NotificationDefinition):
        if not issubclass(definition.schema, NotificationParameters):
            raise ValueError(f'{definition.schema.__name__} is not a {NotificationParameters.__name__}')

        self._value_ = definition.identifier
        self.definition = definition

    @classmethod
    def register(cls, app_config):
        """
        Registers the notifications defined in the app configuration
        """
        try:
            from pushnotif.models.notification import NotificationTemplate
            NotificationTemplate.objects.count()
        except DatabaseError:
            logger.error(f"Unable to notification for {app_config.label}")
            return

        if not hasattr(BaseNotification, '_notifications'):
            BaseNotification._notifications = {}

        for self in cls:
            cls._notifications[self.value] = self
            queryset = NotificationTemplate.objects.filter(name=self.value)

            if queryset.exists():
                queryset.update(
                    app_label=app_config.label,
                    display_name=pydash.human_case(self.value),
                    parameters=self.definition.schema.__qualname__,
                    classname=self.__class__.__qualname__,
                    member=self.name,
                )
            else:
                NotificationTemplate.objects.create(
                    name=self.value,
                    app_label=app_config.label,
                    display_name=pydash.human_case(self.value),
                    parameters=self.definition.schema.__qualname__,
                    classname=self.__class__.__qualname__,
                    member=self.name,
                )

            notification_template = queryset.get()
            notification_template.delivery_method_templates.clear()
            for delivery_method, header, body in self.definition.delivery_method_templates():
                header_template = TemplateModel.from_resource(header)
                body_template = TemplateModel.from_resource(body)
                delivery_method_notification_template = DeliveryMethodNotificationTemplate(
                    header_template=header_template,
                    body_template=body_template,
                    delivery_method=delivery_method.model,
                    notification_template=notification_template,
                )
                delivery_method_notification_template.save()

    @classmethod
    def get_email_by_identifier(cls, identifier: str):
        """
        Retrieves an email by the identifier provided in the app configuration
        """
        return BaseNotification._notifications[identifier]

    def _templates(self) -> Iterable[Tuple[DeliveryMethodNotificationTemplate, Template, Template]]:
        # TODO: Cache this!
        instance: NotificationTemplate = NotificationTemplate.objects.filter(name=self.value).get()
        for delivery_notification_template in DeliveryMethodNotificationTemplate.objects.filter(
                notification_template=instance,
        ):
            header_template = Engine.get_default().get_template(
                template_name=delivery_notification_template.header_template.name)
            body_template = Engine.get_default().get_template(
                template_name=delivery_notification_template.body_template.name)
            yield delivery_notification_template, header_template, body_template

    def render(
            self,
            sender: settings.AUTH_USER_MODEL,
            recipient: settings.AUTH_USER_MODEL,
            parameters: NotificationParameters,
            notification_event: NotificationEvent = None,
            instance: Optional[Model] = None,
    ) -> Iterable[NotificationEventMethod]:
        context = Context(parameters)
        deep_links: dict[DeliveryMethod, str] = DeepLink.get_urls_from_global_id(instance)
        recipient_devices = list(
            DeviceToken.objects.filter(
                recipient_id=recipient.id
            ).order_by('delivery_method').values_list("delivery_method", flat=True).distinct()
        )
        notification_config_validator = NotificationConfigValidator(recipient.profile)

        for delivery_notification_template, header_template, body_template in self._templates():
            try:
                if not notification_config_validator.check_notification_config(delivery_notification_template):
                    continue

                delivery_method = delivery_notification_template.delivery_method
                title: SafeString = header_template.render(context).replace('\n', '')
                body: SafeString = body_template.render(context)
                delivery_method_enum: DeliveryMethods = delivery_method.enum
                notification: Optional[Notification | SMSNotification | EmailNotification | PushNotification] = None
                match delivery_method_enum:
                    case DeliveryMethods.ANDROID | DeliveryMethods.IOS:
                        if delivery_method_enum.name not in recipient_devices:
                            continue
                        deep_link = deep_links.get(delivery_method)
                        data = {"link": deep_link} if deep_link else {}
                        notification: PushNotification = PushNotification.objects.create(
                            title=title,
                            message=body,
                            recipient=recipient,
                            data=data,
                            delivery_method=delivery_method
                        )
                    case DeliveryMethods.EMAIL:
                        if not recipient.email:
                            logger.warning(f'User {recipient.username} does not have an email address')
                            continue
                        notification = EmailNotification.objects.create(
                            title=title,
                            message=body,
                            recipient=recipient,
                        )
                    case DeliveryMethods.SMS:
                        if not recipient.profile.phone_number or not recipient.profile.phone_number.raw_input:
                            logger.warning(f'User {recipient.username} does not have a phone number')
                            continue
                        notification = SMSNotification.objects.create(
                            title=title,
                            message=body,
                            recipient=recipient,
                        )
                    case DeliveryMethods.WEBAPP:
                        notification: Notification = Notification.objects.create(
                            created_by=sender,
                            user=recipient,
                            subject=title,
                            message=body,
                        )
                        if instance is not None:
                            model_name: str = instance._meta.model_name
                            global_id_link: GlobalIDLink = GlobalIDLink.objects.get_or_create_link(
                                instance=instance,
                                name=model_name,
                                description=title,
                            )[0]
                            notification.related_gids.add(global_id_link)

                related_gid = GlobalIDLink.objects.get_or_create_link(
                    instance=notification,
                    name=notification._meta.model_name,
                    description=title,
                )[0]
                notification_event_method = NotificationEventMethod.objects.create(
                    related_gid=related_gid,
                    delivery_method=delivery_method,
                    notification_event=notification_event,
                )
                yield notification_event_method
            except Exception as e:
                notification_event.update_status(status=SentStatus.FAILED, error_message=errors_to_str(e))
                logger.error(f'Error sending notification to {recipient.username}: {delivery_method} {e}')

    def send(
            self,
            sender: settings.AUTH_USER_MODEL,
            recipient: settings.AUTH_USER_MODEL,
            parameters: NotificationParameters,
            instance: Optional[Model] = None,
    ) -> str:
        self.assert_body_schema(parameters=parameters)
        notification_event = NotificationEvent.objects.create(
            recipient=recipient,
            sender=sender,
            status=SentStatus.PENDING,
        )
        for notification_event_method in self.render(
                sender=sender,
                recipient=recipient,
                parameters=parameters,
                instance=instance,
                notification_event=notification_event,
        ):
            try:
                notification_event_method.send()
            except Exception as e:
                notification_event.update_status(status=SentStatus.FAILED, error_message=errors_to_str(e))

    def parameters_sample(self) -> NotificationParameters:
        """
        Generate a random sample body.
        """
        sample = self.definition.schema()
        return sample

    def assert_body_schema(self, parameters: NotificationParameters):
        """
        Verifies that the given body is valid for this email notification.
        """
        if not isinstance(parameters, self.definition.schema):
            raise TypeError(f'{parameters} is not a {self.definition.schema}')

    def __str__(self):
        return f'{self.__class__.__name__}.{self.name}'

    __repr__ = __str__

    __call__ = send


class BroadcastNotification:
    def __init__(
            self,
            notification: BaseNotification | None,
            broadcast_notification: BaseNotification | None,
    ):
        self.notification = notification
        self.broadcastNotification = broadcast_notification

    def __call__(
            self,
            notification_parameters: NotificationParameters,
            sender: settings.AUTH_USER_MODEL,
            recipient: settings.AUTH_USER_MODEL,
            instance: Optional[Model] = None,
            on_behalf_of: settings.AUTH_USER_MODEL = None,
    ):
        if self.notification:
            self.send(self.notification, notification_parameters, sender, recipient, instance)
        if self.broadcastNotification:
            self.broadcast(sender, recipient, instance, on_behalf_of=on_behalf_of)

    def send(
            self,
            notification: BaseNotification,
            parameters: NotificationParameters,
            sender: settings.AUTH_USER_MODEL,
            recipient: settings.AUTH_USER_MODEL,
            instance: Optional[Model] = None
    ):
        notification.send(
            sender=sender,
            recipient=recipient,
            parameters=parameters,
            instance=instance,
        )

    def broadcast(
            self,
            sender: settings.AUTH_USER_MODEL,
            recipient: settings.AUTH_USER_MODEL,
            instance: Optional[Model] = None,
            on_behalf_of: settings.AUTH_USER_MODEL = None,
    ):
        """
        Broadcast notification using registered handlers.

        Domain apps register broadcast handlers via the registry.
        This keeps pushnotif generic and domain-agnostic.
        """
        from pushnotif.broadcast_registry import get_broadcast_handlers

        try:
            notification_type = self.broadcastNotification.name
            template_id = self.broadcastNotification.definition.identifier

            # Call all registered broadcast handlers
            handlers = get_broadcast_handlers()
            for handler in handlers:
                try:
                    handler(
                        sender=sender,
                        recipient=recipient,
                        instance=instance,
                        notification_type=notification_type,
                        template_id=template_id,
                        on_behalf_of=on_behalf_of,
                    )
                except Exception as handler_error:
                    logger.exception(f"Broadcast handler {handler.__name__} failed: {handler_error}")

        except Exception as e:
            logger.exception(f"Broadcast notification failed: {e}")

import abc
import enum
import logging
from dataclasses import dataclass, field
from email.headerregistry import Address as EmailAddress
from typing import Optional

from core.utils.resources import EmbeddedResource
from django.conf import settings
from django.core.mail import EmailMessage
from django.db import DatabaseError
from django.template import Context, Template
from django.template.engine import Engine
from django.utils.safestring import SafeString

logger = logging.getLogger(__name__)


@dataclass
class EmailDefinition:
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
    Default Subject
    """
    header_template: EmbeddedResource

    """
    Template Location
    """
    body_template: EmbeddedResource


@dataclass
class EmailRequest:
    """
    Defines the minimum necessary fields for sending an email
    """
    subject: Optional[str] = None
    recipients: list[EmailAddress] = field(default_factory=list)
    carbon_copy: list[EmailAddress] = field(default_factory=list)
    blind_carbon_copy: list[EmailAddress] = field(default_factory=list)
    sender: Optional[EmailAddress] = None


class EmailParameters(abc.ABC):
    """
    Base class for email Body Compatible for Django Template Context(s)
    """

    def __getitem__(self, item):
        return getattr(self, item)

    def __contains__(self, item):
        return hasattr(self, item)


class BaseEmail(enum.Enum):
    """
    Provides support for listing existing emails inside an application.
    """

    _templates: dict[str, "BaseEmail"]

    def __init__(self, definition: EmailDefinition):
        if not issubclass(definition.schema, EmailParameters):
            raise ValueError(f'{definition.schema.__name__} is not a {EmailParameters.__name__}')

        self._value_ = definition.identifier
        self.definition = definition
        self._body_template: Optional[Template] = None
        self._header_template: Optional[Template] = None

    @classmethod
    def register(cls, app_config):
        """
        Registers the emails defined in the app configuration
        """
        try:
            from core.models import EmailTemplate, TemplateModel
            EmailTemplate.objects.count()
            TemplateModel.objects.count()
        except DatabaseError:
            logger.error(f"Unable to register emails for {app_config.label}")
            return
        if not hasattr(BaseEmail, '_templates'):
            BaseEmail._templates = {}
        for self in cls:
            cls._templates[self.value] = self
            queryset = EmailTemplate.objects.filter(id=self.value)
            header_template = TemplateModel.from_resource(self.definition.header_template)
            body_template = TemplateModel.from_resource(self.definition.body_template)
            if queryset.exists():
                queryset.update(
                    app_label=app_config.label,
                    classname=self.__class__.__qualname__,
                    member=self.name,
                    parameters=self.definition.schema.__qualname__,
                    header_template=header_template,
                    body_template=body_template,
                )
            else:
                EmailTemplate.objects.create(
                    id=self.value,
                    app_label=app_config.label,
                    classname=self.__class__.__qualname__,
                    member=self.name,
                    parameters=self.definition.schema.__qualname__,
                    header_template=header_template,
                    body_template=body_template,
                )

    @classmethod
    def get_email_by_identifier(cls, identifier: str):
        """
        Retrieves an email by the identifier provided in the app configuration
        """
        return BaseEmail._templates[identifier]

    @property
    def body_template(self) -> Template:
        """
        Loads the body template of this email definition.
        """
        if self._body_template is None:
            self._body_template = Engine.get_default().get_template(
                template_name=self.definition.body_template.name
            )
        return self._body_template

    @property
    def header_template(self) -> Template:
        """
        Loads the header template of this email definition.
        """
        if self._header_template is None:
            self._header_template = Engine.get_default().get_template(
                template_name=self.definition.header_template.name
            )
        return self._header_template

    def send(
            self,
            request: EmailRequest,
            parameters: EmailParameters,
    ) -> str:
        """
        Sends an email with the given parameters and to the recipients provided
        """
        logger.info(f'{request} requested')
        self.assert_body_schema(parameters=parameters)
        subject: SafeString = request.subject or self.render_header(parameters=parameters)
        body: SafeString = self.render(parameters=parameters)
        sender = request.sender or EmailAddress(addr_spec=settings.FROM_EMAIL)
        email = EmailMessage(
            subject=subject,
            from_email=str(sender),
            to=[str(address) for address in request.recipients],
            cc=[str(address) for address in request.carbon_copy],
            bcc=[str(address) for address in request.blind_carbon_copy],
            body=body,
        )
        email.content_subtype = 'html'
        email.send(fail_silently=False)
        logger.info(f'{request} processed')

    def render(self, parameters: EmailParameters) -> SafeString:
        """
        Renders the given parameters.
        """
        context = Context(parameters)
        body = self.body_template.render(context=context)
        return body

    def render_header(self, parameters: EmailParameters) -> SafeString:
        """
        Renders the given parameters.
        """
        context = Context(parameters)
        body = self.header_template.render(context=context)
        return body

    def parameters_sample(self) -> EmailParameters:
        """
        Generate a random sample body.
        """
        sample = self.definition.schema()
        return sample

    def assert_body_schema(self, parameters: EmailParameters):
        """
        Verifies that the given body is valid for this email notification.
        """
        if not isinstance(parameters, self.definition.schema):
            raise TypeError(f'{parameters} is not a {self.definition.schema}')

    def __str__(self):
        return f'{self.__class__.__name__}.{self.name}'

    __repr__ = __str__

    __call__ = send

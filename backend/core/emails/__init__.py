import dataclasses

from core.systems import BaseEmail, EmailDefinition, EmailParameters
from core.utils.resources import EmbeddedResource


class EmailResources(EmbeddedResource):
    """
    Core resource files
    """

    welcome_email_body = "welcome_email_body.html"
    welcome_email_header = "welcome_email_header.html"


@dataclasses.dataclass
class WelcomeEmailParameters(EmailParameters):
    """
    Welcome email body.
    """

    first_name: str = 'John'

    last_name: str = 'Doe'


class Emails(BaseEmail):

    WELCOME = EmailDefinition(
        identifier="welcome",
        header_template=EmailResources.welcome_email_header,
        body_template=EmailResources.welcome_email_body,
        schema=WelcomeEmailParameters,
    )

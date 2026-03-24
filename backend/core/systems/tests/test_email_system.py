from email.headerregistry import Address
from unittest import TestCase
from unittest.mock import patch

from core.emails import Emails
from core.models import EmailTemplate
from core.systems import EmailRequest
from django.apps import apps


class EmailSystemTests(TestCase):

    def setUp(self):
        app_config = apps.get_app_config('core')
        Emails.register(app_config)

    def test_register_email_system(self):
        for email in Emails:
            email_template: EmailTemplate = EmailTemplate.objects.filter(id=email.value).first()
            assert email_template
            assert email_template.body_template
            assert email_template.header_template
            assert email_template.member == email.name
            assert email_template.classname == Emails.__qualname__

    def test_render_email_template(self):
        for email in Emails:
            sample = email.parameters_sample()
            assert sample
            body = email.render(sample)
            assert body

    def test_send_email(self):
        for email in Emails:
            sample = email.parameters_sample()
            with patch('django.core.mail.EmailMessage.send') as send:
                email.send(
                    request=EmailRequest(
                        subject="Test Subject",
                        recipients=[Address(addr_spec='user@domain.com')],
                    ),
                    parameters=sample,
                )
                send.assert_called_once()

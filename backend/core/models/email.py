"""
Email Related Models
"""

from django.db import models

from .template import TemplateModel


class EmailTemplate(models.Model):
    """
    Keeps track of the email templates registered in the system
    """

    id = models.CharField(primary_key=True, max_length=128)

    app_label = models.CharField(max_length=128, null=False, blank=False)

    classname = models.CharField(max_length=1024, null=False, blank=False)

    member = models.CharField(max_length=128, null=False, blank=False)

    parameters = models.CharField(max_length=1024, null=False, blank=False)

    header_template = models.ForeignKey(
        TemplateModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='header_templates',
        help_text='Group of email which this email template belongs to as the header.')

    body_template = models.ForeignKey(
        TemplateModel,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='body_templates',
        help_text='Group of email which this email template belongs to as the body.')

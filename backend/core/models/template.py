"""
Template Related Models
"""

from core.utils.resources import EmbeddedResource
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class TemplateModel(models.Model):
    """
    Defines a template model for use with the database template loader.
    The field ``name`` is the equivalent to the filename of a static template.
    """

    class Meta:
        verbose_name = _('template')
        verbose_name_plural = _('templates')
        ordering = ('name',)

    name = models.CharField(
        _('name'),
        max_length=256,
        primary_key=True,
    )

    content = models.TextField(
        _('content'),
        blank=True,
    )

    creation_date = models.DateTimeField(
        _('creation date'),
        default=now,
    )

    last_changed = models.DateTimeField(
        _('last changed'),
        default=now
    )

    @classmethod
    def from_resource(cls, resource: EmbeddedResource) -> "TemplateModel":
        """
        Loads a template from the give EmbeddedResource object.
        """
        record = cls.objects.filter(name=resource.name).first()
        if record is None:
            record = TemplateModel.objects.create(
                name=resource.name,
                content=resource.content,
            )
        else:
            record.content = resource.content
            record.save()
        return record

    def __str__(self):
        return self.name

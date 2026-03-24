"""
Application Related Models
"""

from django.db import models

from .common import BaseCoreModel


class Application(BaseCoreModel):
    name = models.CharField(max_length=50, blank=True)
    description = models.CharField(max_length=256, blank=True)

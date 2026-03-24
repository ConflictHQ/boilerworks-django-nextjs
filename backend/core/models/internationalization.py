from core.models import Tracking
from django.db import models


class Locale(models.Model):
    """Locale model for internationalization."""
    language_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=64, blank=True, default='')

    def __str__(self):
        return self.language_code

    class Meta:
        app_label = 'core'


class SiteLabel(Tracking):
    class Meta:
        unique_together = ('key', 'locale')

    key = models.CharField(blank=False, db_index=True, max_length=150, null=False)
    locale = models.ForeignKey(Locale, on_delete=models.SET_NULL, null=True, blank=True)
    text = models.TextField(null=False, blank=True, default='')

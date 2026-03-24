import enum
import logging
import time

import jwt
from django.conf import settings
from django.db import models

from .common import Tracking

logger = logging.getLogger(__name__)


class ReportType(enum.Enum):
    """
    Enumeration of charts / reports types.
    """
    DASHBOARD = 'dashboard'
    QUESTION = 'question'

    def __str__(self):
        return self.value


class MetabaseChart(Tracking):
    type = models.CharField(
        max_length=32,
        choices=[(report_type.name, report_type.value) for report_type in ReportType],
        default=ReportType.DASHBOARD.value
    )

    metabase_chart_id = models.IntegerField(
        blank=False, null=False
    )

    title = models.CharField(
        max_length=250,
        blank=False,
        null=False
    )

    description = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    @property
    def iframe_url(self):
        metabase_token = settings.METABASE_SECRET_KEY
        report_type_display_value = self.get_type_display()

        payload = {
            "resource": {report_type_display_value: self.metabase_chart_id},
            "params": {},
            "exp": round(time.time()) + (60 * 10)  # 10 minute expiration
        }

        logger.info("Metabase payload = " + str(payload))

        token = jwt.encode(payload, metabase_token, algorithm="HS256")
        metabase_url = settings.METABASE_SITE_URL
        iframe_url = f"{metabase_url}/embed/{report_type_display_value}/{token}"

        logger.info("Metabase iframeURL = " + iframe_url)

        return iframe_url

    @classmethod
    def set_embedding_enabled(self, metabase_chart_id, type: ReportType):
        from core.utils.api.metabase_rest_client import MetabaseRestClient

        metabase_rest_client = MetabaseRestClient()

        return metabase_rest_client.set_chart_as_embedding_enabled(metabase_chart_id, type)

    class Meta:
        unique_together = ['metabase_chart_id', 'type']

        ordering = ['-created_at']
        verbose_name = 'Metabase Chart'
        verbose_name_plural = 'Metabase Charts'

        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['metabase_chart_id']),
            models.Index(fields=['created_at']),
        ]

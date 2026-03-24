import enum
import logging

from core.models import MetabaseChart, ReportType
from django.db import models
from django.db.models import signals
from django.dispatch import receiver

logger = logging.getLogger(__name__)


class MetabaseObjectType(enum.Enum):
    """
    Enumeration of charts / reports types.
    """
    DASHBOARD = 'dashboard'
    QUESTION = 'question'

    def __str__(self):
        return self.value


class MetabaseUnimportedChart(models.Model):
    id = models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')

    metabase_chart_id = models.IntegerField(
        blank=False, null=False
    )

    type = models.CharField(
        max_length=32,
        choices=[(object_type.name, object_type.value) for object_type in MetabaseObjectType],
        default=MetabaseObjectType.DASHBOARD.value
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

    creator_email = models.CharField(
        max_length=100,
        blank=False,
        null=False
    )

    is_embedding_enabled = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=False
    )

    is_chart_imported = models.BooleanField(default=False)

    @classmethod
    def retrieve_and_save_unimported_metabase_charts(self):
        from core.utils.api.metabase_rest_client import MetabaseRestClient

        metabase_rest_client = MetabaseRestClient()
        metabase_rest_client.get_and_save_unimported_metabase_charts()

        return 'success'

    @staticmethod
    @receiver(signals.post_save, sender=MetabaseChart)
    def on_chart_save(sender, instance, created, **kwargs):
        if created:
            try:
                unimported_instance = MetabaseUnimportedChart.objects.get(metabase_chart_id=instance.metabase_chart_id, type=instance.type)
                unimported_instance.is_chart_imported = True
                unimported_instance.save(update_fields=['is_chart_imported'])
                return MetabaseUnimportedChart.set_embedding_enabled(instance.metabase_chart_id, instance.type)
            except MetabaseUnimportedChart.DoesNotExist:
                logger.warning(
                    f'MetabaseUnimportedChart not found for chart id: {instance.metabase_chart_id} '
                    f'and type: {instance.type} — chart was imported outside the unimported queue'
                )
                return

    @staticmethod
    def set_embedding_enabled(metabase_chart_id, type: ReportType):
        response = MetabaseChart.set_embedding_enabled(metabase_chart_id, type)

        if response.get('success', False) is False:
            logger.error(f'Failed to set embedding enabled for Metabase chart id: {metabase_chart_id} and type: {type}')

        return response

    class Meta:
        unique_together = ['metabase_chart_id', 'type']

        ordering = ['-created_at']
        verbose_name = 'Metabase Unimported Chart'
        verbose_name_plural = 'Metabase Unimported Charts'

        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['metabase_chart_id']),
        ]

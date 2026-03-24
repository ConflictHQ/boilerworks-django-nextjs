from django.apps import apps
from django.db import models


class ApprovalPropertyWhitelist(models.Model):
    content_type = models.ForeignKey(
        'contenttypes.ContentType',
        related_name='approval_whitelists',
        on_delete=models.CASCADE
    )
    attribute = models.CharField(
        max_length=50,
        null=False,
        blank=False,
    )
    enabled = models.BooleanField(
        default=True,
    )

    class Meta:
        unique_together = ('content_type', 'attribute')

    def save(self, *args, **kwargs):
        model = apps.get_model(self.content_type.app_label, self.content_type.model)
        if not hasattr(model, self.attribute):
            valid_fields = [f.name for f in model._meta.get_fields()]
            raise AttributeError(
                f"{self.content_type.model} object has no attribute '{self.attribute}'."
                f" Available options include:{valid_fields}"
            )
        if hasattr(model, 'whitelist_fields') and callable(getattr(model, 'whitelist_fields')):
            model.whitelist_fields.cache_clear()
        super().save(*args, **kwargs)

import uuid

from django.db import models

from .common import Tracking

__all__ = ['ORGANIZATION_PLACEHOLDER', 'SupersetDashboard']

# Placeholder in `rls_clause` that the guest token fills with the requesting
# user's active organization guid (quoted). See SupersetDashboard.rls_clause.
ORGANIZATION_PLACEHOLDER = '{organization_guid}'


class SupersetDashboard(Tracking):
    """A Superset dashboard the app embeds through the Superset Embedded SDK.

    `embedded_id` is the UUID Superset shows under "Embed dashboard" (it is not
    the dashboard's numeric id). The browser only ever receives this UUID and a
    short-lived guest token issued by the backend.
    """

    guid = models.UUIDField(editable=False, default=uuid.uuid4, unique=True)

    embedded_id = models.UUIDField(
        unique=True,
        help_text='Embedded dashboard UUID from Superset ("Embed dashboard").',
    )

    title = models.CharField(max_length=250)

    description = models.CharField(max_length=250, blank=True, null=True)

    order = models.PositiveIntegerField(default=0, help_text='Position in the analytics page (lowest first).')

    rls_clause = models.TextField(
        blank=True,
        default='',
        help_text=(
            'Optional row-level security clause added to the guest token, e.g. '
            f'"organization_guid = {ORGANIZATION_PLACEHOLDER}". The placeholder becomes the '
            "user's active organization guid; users without one see no rows."
        ),
    )

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Superset Dashboard'
        verbose_name_plural = 'Superset Dashboards'

    def __str__(self):
        return self.title

    def rls_rules(self, user):
        """Row-level security rules for a guest token issued to `user`."""
        clause = self.rls_clause.strip()
        if not clause:
            return []
        if ORGANIZATION_PLACEHOLDER in clause:
            organization = user.profile.organization() if hasattr(user, 'profile') else None
            if organization is None:
                return [{'clause': '1 = 0'}]
            # A UUID has no quotes or SQL metacharacters, so quoting it is safe.
            clause = clause.replace(ORGANIZATION_PLACEHOLDER, f"'{uuid.UUID(str(organization.guid))}'")
        return [{'clause': clause}]

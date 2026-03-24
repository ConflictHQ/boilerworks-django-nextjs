from core.models.common import BaseCoreModel, Tracking
from django.conf import settings
from django.contrib.auth.models import Group
from django.db import models
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils.text import slugify


class Organization(BaseCoreModel):

    website = models.URLField(blank=True, null=True)
    search = models.TextField(max_length=500, null=True, blank=True,)
    groups = models.ManyToManyField(Group, blank=True, related_name='organizations')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)

        self.search = f'{self.name} {self.slug} {self.website}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name}'


@receiver(m2m_changed, sender=Organization.groups.through)
def sync_org_groups(sender, instance, action, model, pk_set, **kwargs):
    if action == "post_remove":
        for group_pk in iter(pk_set):
            group = model.objects.get(pk=group_pk)
            instance.member.groups.remove(group)


class OrganizationMember(Tracking):
    is_active = models.BooleanField(default=True, help_text='Is active in the organization')

    member = models.ForeignKey(settings.AUTH_USER_MODEL,
                               related_name='memberships', db_index=True,
                               null=True, blank=True, on_delete=models.CASCADE)

    organization = models.ForeignKey(Organization,
                                     related_name='members',
                                     null=True, blank=True, on_delete=models.CASCADE)

    groups = models.ManyToManyField(Group, blank=True, related_name='memberships',
                                    help_text='Member groups in the organization')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.organization}/{self.member}'


@receiver(m2m_changed, sender=OrganizationMember.groups.through)
def sync_org_member_groups(sender, instance, action, model, pk_set, **kwargs):
    if action == "post_add":
        for group_pk in iter(pk_set):
            group = model.objects.get(pk=group_pk)
            instance.member.groups.add(group)

    if action == "post_remove":
        for group_pk in iter(pk_set):
            group = model.objects.get(pk=group_pk)
            instance.member.groups.remove(group)

    if action == "pre_add":
        for group_pk in iter(pk_set):
            group = model.objects.get(pk=group_pk)
            if not instance.organization.groups.filter(pk=group.pk).exists():
                raise Exception('Only groups from the same organization can be assigned to a member')

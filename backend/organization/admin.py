import nested_admin
from core.utils.admin import AdminGrapheneUtils, BaseCoreAdmin
from django.contrib import admin
from django.contrib.auth.models import Group
from organization.models import Organization, OrganizationMember


class GroupInline(nested_admin.NestedStackedInline):
    model = Group


class OrganizationMemberInline(nested_admin.NestedTabularInline):
    model = OrganizationMember
    exclude = 'version', 'created_by', 'last_modified_by',
    extra = 0
    show_change_link = True


@admin.register(Organization)
class OrganizationAdmin(BaseCoreAdmin, nested_admin.NestedModelAdmin, AdminGrapheneUtils):
    list_display = 'name', 'slug', 'created_by', 'global_id',
    ordering = 'name',
    search_fields = 'name', 'slug', 'website',
    filter_horizontal = 'groups',


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(BaseCoreAdmin, admin.ModelAdmin, AdminGrapheneUtils):
    list_display = 'organization', 'member', 'global_id',
    ordering = 'organization', 'member',
    filter_horizontal = 'groups',
    search_fields = 'organization__name', 'member__username',
    raw_id_fields = 'member',
    list_filter = 'organization',

    def get_queryset(self, request):
        queryset = super(OrganizationMemberAdmin, self).get_queryset(request)
        queryset = queryset.select_related('organization', 'member')
        return queryset


class GroupAdmin(nested_admin.NestedModelAdmin, AdminGrapheneUtils):
    pass

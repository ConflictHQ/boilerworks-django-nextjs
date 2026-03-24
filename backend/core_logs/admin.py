import json
from datetime import timedelta
from textwrap import dedent

from core.utils.admin import obj_to_link, objs_to_links
from core_logs.models import GQLLog, PermissionAccessLog
from django.contrib import admin, messages
from django.utils.safestring import mark_safe

# Optional import - domain app functionality
try:
    from domain_app.models import DepartmentEmployee
    HAS_DOMAIN_APP = True
except ImportError:
    HAS_DOMAIN_APP = False


@admin.register(PermissionAccessLog)
class PermissionAccessLogAdmin(admin.ModelAdmin):
    list_display = 'user', 'permission', 'created_at', 'access',
    list_filter = 'access',
    search_fields = 'user__username', 'permission__name', 'permission__codename'
    readonly_fields = 'organization', 'user', 'permission', 'created_at', 'access', 'description', \
                      'user_groups', 'position_groups',
    ordering = '-created_at',

    def user_groups(self, obj):
        html = self._html_groups(obj, obj.user.groups)
        return mark_safe(html)

    def position_groups(self, obj):
        """
        Display position groups (domain app-specific).

        This field only shows data when domain_app is available.
        """
        if not HAS_DOMAIN_APP:
            return mark_safe('<i>Domain app features not available</i>')

        dep_positions = DepartmentEmployee.objects.filter_by_user(obj.user)\
            .select_related('position')\
            .prefetch_related('position__groups').order_by('position__name')

        html = ''
        for dep_pos in dep_positions:
            html += f'{dep_pos}:<br/>'
            html += self._html_groups(obj, dep_pos.position.groups)

        return mark_safe(html if html else '<i>No positions found</i>')

    @classmethod
    def _html_groups(cls, obj, groups):
        groups_with_permission = groups.filter(permissions=obj.permission).order_by('name')
        groups_without_permission = groups.exclude(permissions=obj.permission).order_by('name')
        html = '<b>&nbsp;&nbsp;With Permission:</b><br/>'
        if groups_with_permission:
            html += objs_to_links(groups_with_permission).replace('<br/>', '<br/>&nbsp;&nbsp;')
        else:
            html += '&nbsp;&nbsp;None<br/>'
        html += '<br/>&nbsp;&nbsp;Without Permission:<br/>'
        if groups_without_permission:
            html += objs_to_links(groups_without_permission).replace('<br/>', '<br/>&nbsp;&nbsp;')
        else:
            html += '&nbsp;&nbsp;None<br/>'
        return html


class GQLLogStatusFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Status"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "status"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [
            ("success", 'Success'),
            ("error", 'Error'),
        ]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "success":
            return queryset.filter(
                error__isnull=True,
            )
        if self.value() == "error":
            return queryset.filter(
                error__isnull=False,
            )


class GQLLogOrganizationFilter(admin.RelatedOnlyFieldListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = "Organization"

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "organization"

    def has_output(self):
        return True

    def choices(self, changelist):
        result = list(super(GQLLogOrganizationFilter, self).choices(changelist))
        default_index = -1
        selected_index = -1
        for index, choice in enumerate(result):
            if choice['selected']:
                selected_index = index
            if 'BoilerWorks' in choice['display']:
                default_index = index
        if selected_index == 0 and default_index >= 0:
            result[selected_index]['selected'] = False
            result[default_index]['selected'] = True
        return result


@admin.register(GQLLog)
class GQLLogAdmin(admin.ModelAdmin):
    list_display = 'pk', '_user', 'organization', '_duration_ms', 'operation_name', 'status',  '_replayed_from', 'created_at',
    list_filter = [
        GQLLogStatusFilter,
        ('organization', GQLLogOrganizationFilter),
        'operation_name',
    ]
    ordering = '-created_at',
    readonly_fields = '_duration_millis', 'gql_url', '_user', 'replayed_from', '_result', 'error',
    actions = 'execute_with_current_user', 'execute',

    def lookup_allowed(self, key, value, request=None):
        if key in (
                'user__username__istartswith',
                'operation_name__istartswith',
                'query__icontains',
                'variables__icontains',
                'response__icontains'
        ):
            return True
        return super(GQLLogAdmin, self).lookup_allowed(key, value, request=request)

    def _duration_ms(self, obj: GQLLog):
        if obj.duration_millis is None:
            return ''
        return f'{obj.duration_millis}'

    def _duration_millis(self, obj: GQLLog):
        if obj.duration_millis is None:
            return ''
        time = timedelta(milliseconds=obj.duration_millis)
        return f'({time}) or ({obj.duration_millis}ms)'

    def _user(self, obj: GQLLog):
        if obj.switch_user:
            return obj_to_link(obj.user, f'{obj.switch_user}/{obj.user}')
        return obj_to_link(obj.user, obj.user.username)

    def has_add_permission(self, request, obj=None):
        return False

    def gql_url(self, obj: GQLLog):
        from core.tests.utils.document_writer import url_gql_encode
        url = url_gql_encode(None, dedent(obj.query).encode(), json.dumps(obj.variables).encode())
        return mark_safe(f'<a target="_blank" href="{url}">Open In GQL</a>')

    def status(self, obj: GQLLog):
        return 'Error' if obj.error else 'Success'

    def _replayed_from(self, obj: GQLLog):
        return obj_to_link(obj.replayed_from, f'{obj.replayed_from.pk if obj.replayed_from else None}')

    def execute_with_current_user(self, request, queryset):
        for obj in queryset:
            response = obj.execute(request, request.user)
            messages.info(request, f'Executed {obj} with response {response}')

    def execute(self, request, queryset):
        for obj in queryset:
            response = obj.execute(request)
            messages.info(request, f'Executed {obj} with response {response}')

    def _result(self, obj):
        json_data = getattr(obj, 'response', {})
        pretty_json = json.dumps(json_data, indent=2)
        return mark_safe(f'<pre>{pretty_json}</pre>')

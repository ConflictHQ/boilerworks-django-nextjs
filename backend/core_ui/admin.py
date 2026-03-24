from core.utils.admin import BaseCoreAdmin
from core_ui.models import Component
from django.contrib import admin
from django.utils import timezone


class ComponentRelationshipInline(admin.TabularInline):
    model = Component.components.through
    fields = ('order', 'parent', 'child',)
    ordering = ('order',)
    fk_name = 'parent'
    extra = 1


@admin.register(Component)
class ComponentAdmin(BaseCoreAdmin):
    list_display = 'slug', 'children', 'is_active', 'global_id',
    list_filter = ('is_active',)
    search_fields = ('name', 'path')
    ordering = ('slug',)
    filter_horizontal = ('permissions',)
    inlines = ComponentRelationshipInline,
    actions = ['sync_permissions', 'export_all_components']

    @admin.action(description='Sync Permissions')
    def sync_permissions(self, request, queryset):
        for component in queryset:
            component.syn_permissions()

    @admin.action(description='Export all components to CSV')
    def export_all_components(self, request, queryset=None):
        import csv

        from django.http import HttpResponse

        response = HttpResponse(content_type='text/csv')
        filename = f"components_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        writer = csv.writer(response)
        writer.writerow([
            'Name',
            'Slug',
            'Description',
            'Is Active',
            'Path',
            'Icon',
            'Properties',
            'Permissions',
            'Children',
        ])

        for component in Component.objects.all():
            permissions = '|'.join([
                f'{permission.content_type.model}.{permission.content_type.app_label}.{permission.codename}'
                for permission in component.permissions.all()
            ])
            children = '|'.join([child.slug for child in component.ordered_components])
            writer.writerow([
                component.name,
                component.slug,
                component.description,
                component.is_active,
                component.path,
                component.icon,
                component.properties,
                permissions,
                children,
            ])
        return response

    def children(self, obj):
        return obj.components.count()

from django.contrib import admin, messages
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.safestring import mark_safe
from graphene_django.registry import get_global_registry
from import_export.admin import ImportExportMixin


class AdminGrapheneUtils:

    @classmethod
    def global_id(cls, obj):
        registry = get_global_registry()
        schema_type = registry.get_type_for_model(type(obj))
        return schema_type and registry.get_type_for_model(type(obj)).to_global_id(obj) or 'Not Defined'


class BaseCoreMixing:

    def get_raw_id_fields(self, request):
        return ((self.raw_id_fields or ()) + ('created_by', 'updated_by', 'deleted_by', 'deleted_at'))

    def get_readonly_fields(self, request, obj=None):
        # if obj is not None, this means we're editing an existing object rather than adding a new one
        return ((self.readonly_fields or ()) +
                ('global_id', 'version', 'created_at', 'created_by', 'updated_by', 'updated_at', 'deleted_at',
                 'deleted_by'))
        # return super().get_readonly_fields(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if hasattr(self.model, 'to_mermaid'):  # Example condition
            actions['diagram'] = (self.diagram, 'diagram', 'Generate Mermaid diagram')
        return actions

    def diagram(self, admin, request, queryset, *args, **kwargs):
        content_type = ContentType.objects.get_for_model(queryset[0])
        for rule in queryset:
            url = reverse('diagram_view', kwargs=dict(
                content_type_id=content_type.id,
                object_id=rule.id
            ))
            messages.info(request, mark_safe(f'<a target="_blank" href="{url}">Diagram {rule}</a>'))


class BaseCoreAdmin(admin.ModelAdmin, AdminGrapheneUtils, BaseCoreMixing, ImportExportMixin):

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        self.raw_id_fields = self.get_raw_id_fields(request)
        self.readonly_fields = self.get_readonly_fields(request, obj)
        return form

    def save_model(self, request, obj, form, change):
        # If the object is being created, set the user as the creator
        if hasattr(obj, 'created_by') and not obj.created_by:
            obj.created_by = request.user

        if hasattr(obj, 'updated_by'):
            obj.updated_by = request.user

        super().save_model(request, obj, form, change)


def obj_to_link(obj, label=None):
    if not obj:
        return None

    app_label = obj._meta.app_label
    model_name = obj._meta.model_name
    url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.pk])
    label = label or str(obj)
    return mark_safe(f'<a target="_blank" href="{url}">{label}</a>')


def objs_to_links(objs):
    urls = ''.join([f'<li>{obj_to_link(obj)}</li>' for obj in objs])
    return mark_safe(f'<ul>{urls}</ul>')


def timedelta_to_str(td):
    return f'{int(td.seconds / 60)}:{td.seconds % 60}'

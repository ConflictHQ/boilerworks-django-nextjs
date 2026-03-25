from core.utils.admin import BaseCoreAdmin
from core.widgets import JSONEditorWidget, WorkflowStatesWidget, WorkflowTransitionsWidget
from django.contrib import admin
from django.db import models
from django.utils.html import format_html

from .models import TransitionLog, WorkflowDefinition, WorkflowInstance


class TransitionLogInline(admin.TabularInline):
    model = TransitionLog
    extra = 0
    readonly_fields = ('from_state', 'to_state', 'transitioned_by', 'note', 'timestamp')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(WorkflowDefinition)
class WorkflowDefinitionAdmin(BaseCoreAdmin):
    list_display = ('name', 'slug', 'model_label', 'state_count', 'is_enabled', 'instance_count')
    list_filter = ('is_enabled', 'model_label')
    search_fields = ('name', 'slug', 'model_label')
    formfield_overrides = {models.JSONField: {'widget': JSONEditorWidget}}

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'states':
            kwargs['widget'] = WorkflowStatesWidget
            return db_field.formfield(**kwargs)
        if db_field.name == 'transitions':
            kwargs['widget'] = WorkflowTransitionsWidget
            return db_field.formfield(**kwargs)
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    def state_count(self, obj):
        return len(obj.states)
    state_count.short_description = 'States'

    def instance_count(self, obj):
        return obj.instances.count()
    instance_count.short_description = 'Instances'


@admin.register(WorkflowInstance)
class WorkflowInstanceAdmin(admin.ModelAdmin):
    list_display = ('pk', 'workflow', 'current_state', 'object_id', 'is_completed_badge', 'started_at')
    list_filter = ('workflow', 'current_state')
    readonly_fields = ('workflow', 'content_type', 'object_id', 'current_state', 'started_at', 'completed_at')
    inlines = [TransitionLogInline]

    def is_completed_badge(self, obj):
        if obj.completed_at:
            return format_html('<span style="color:green;">✓</span>')
        return format_html('<span style="color:gray;">○</span>')
    is_completed_badge.short_description = 'Done'

import logging

from core.utils.admin import BaseCoreAdmin, timedelta_to_str
from core.utils.logger_helper import InMemoryLogHandler
from core_rule_engine.models import (
    ActionDefinition,
    ActionExecution,
    ConditionDefinition,
    ConditionExecution,
    Payload,
    RuleDefinition,
    RuleExecution,
    RuleModelSignal,
    RuleProviderDefinition,
)
from django.contrib import admin, messages
from django.utils import timezone
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)


class ConditionDefinitionInline(admin.TabularInline):
    fields = ('slug', 'enabled')
    readonly_fields = ('slug',)
    model = ConditionDefinition
    extra = 0


class ActionDefinitionInline(admin.TabularInline):
    fields = ('slug', 'enabled')
    readonly_fields = ('slug',)
    model = ActionDefinition
    extra = 0


@admin.register(RuleProviderDefinition)
class RuleProviderDefinitionAdmin(admin.ModelAdmin):
    list_display = ('app_label', 'slug', )
    search_fields = ('app_label', 'slug',)
    inlines = [ConditionDefinitionInline, ActionDefinitionInline]
    readonly_fields = ('app_label', 'slug',)


@admin.register(Payload)
class PayloadAdmin(admin.ModelAdmin):
    list_display = ('slug', 'description')
    search_fields = ('slug', 'description',)


@admin.register(ConditionDefinition)
class ConditionDefinitionAdmin(admin.ModelAdmin):
    list_display = ('rule_provider', 'slug', 'enabled')
    search_fields = ('slug',)


@admin.register(ActionDefinition)
class ActionDefinitionAdmin(admin.ModelAdmin):
    list_display = ('rule_provider', 'slug', 'enabled')
    search_fields = ('slug', )


class ConditionPositionInline(admin.TabularInline):
    fields = ('condition', 'position')
    model = RuleDefinition.conditions.through
    extra = 0
    ordering = ('position',)


class ActionPositionInline(admin.TabularInline):
    fields = ('action', 'position')
    model = RuleDefinition.actions.through
    extra = 0
    ordering = ('position',)


@admin.register(RuleModelSignal)
class RuleSignalAdmin(BaseCoreAdmin):
    list_display = ('when', 'content_type', '_last_executed', '_last_registered')
    search_fields = ('rules__slug', 'when')
    ordering = ('-created_at',)
    list_filter = ('when',)
    filter_horizontal = ('rules',)
    actions = ['register_signals',]

    def _last_registered(self, obj):
        if obj.last_registered is None:
            return 'Never'

        time_diff = timezone.now() - obj.last_registered
        return timedelta_to_str(time_diff)

    def _last_executed(self, obj):
        if obj.last_executed is None:
            return 'Never'

        time_diff = timezone.now() - obj.last_executed
        return timedelta_to_str(time_diff)

    def register_signals(self, request, queryset):
        for rule_signal in queryset:
            rule_signal.register_signals()


@admin.register(RuleDefinition)
class RuleDefinitionAdmin(BaseCoreAdmin):
    list_display = ('slug', 'operant', 'run_on_task', 'enabled',)
    search_fields = ('slug', 'conditions__slug', 'actions__slug',)
    filter_horizontal = ('post_transaction_actions', 'payload',)
    inlines = [ConditionPositionInline, ActionPositionInline]
    fields = ('enabled', 'name', 'slug',
              'operant', 'payload', 'post_transaction_actions',
              'description', 'run_on_task',)
    actions = ('eval_rule', 'eval_conditions', 'eval_actions',)

    def eval_rule(self, request, queryset):
        for rule in queryset:
            try:
                mem_logger = InMemoryLogHandler.get_logger(f'{rule.slug}')
                rule.eval(context={'request': request}, logger=mem_logger, dry_run=True)
                messages.info(request, mark_safe(mem_logger.handlers[0].to_html()))
            except Exception as e:
                logger.exception(f'Error: {e}')
                messages.error(request, f'{rule} - Error: {e}')

    def eval_conditions(self, request, queryset):
        for rule in queryset:
            try:
                mem_logger = InMemoryLogHandler.get_logger(f'{rule.slug}')
                rule.eval_conditions(context={'request': request}, logger=mem_logger, dry_run=True)
                messages.info(request, mark_safe(mem_logger.handlers[0].to_html()))
            except Exception as e:
                logger.exception(f'Error: {e}')
                messages.error(request, f'{rule} - Error: {e}')

    def eval_actions(self, request, queryset):
        for rule in queryset:
            try:
                mem_logger = InMemoryLogHandler.get_logger(f'{rule.slug}')
                rule.eval_actions(context={'request': request}, logger=mem_logger, dry_run=True)
                messages.info(request, mark_safe(mem_logger.handlers[0].to_html()))
            except Exception as e:
                logger.exception(f'Error: {e}')
                messages.error(request, f'{rule} - Error: {e}')


@admin.register(RuleExecution)
class RuleExecutionAdmin(admin.ModelAdmin):
    list_display = ('rule', 'success', 'created_at', )
    search_fields = ('rule__slug',)
    list_filter = ('success',)
    ordering = ('-created_at',)
    actions = ['run_rule']

    def run_rule(self, request, queryset):
        for rule_execution in queryset:
            rule_execution.run_rule()
    run_rule.short_description = 'Run Rule'


@admin.register(ConditionExecution)
class ConditionExecutionAdmin(admin.ModelAdmin):
    list_display = ('condition', 'success', 'created_at',)
    search_fields = ('condition__slug',)
    list_filter = ('success',)
    ordering = ('-created_at',)


@admin.register(ActionExecution)
class ActionExecutionAdmin(admin.ModelAdmin):
    list_display = ('action', 'created_at',)
    search_fields = ('action__slug',)
    list_filter = ('success',)
    ordering = ('-created_at',)

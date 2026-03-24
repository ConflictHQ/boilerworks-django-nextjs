import logging
from typing import cast

from core.models import BaseCoreModel, Tracking
from core.utils.diagrams import FlowchartBuilder
from core.utils.signal_helper import ModelSignalHelper, SignalChoices
from core_rule_engine import tasks
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from .rules import engine

local_logger = logging.getLogger(__name__)


class Payload(models.Model):
    """
    """
    slug = models.SlugField(max_length=100, unique=True)
    payload = models.JSONField(default=dict)
    description = models.TextField(max_length=100, null=True, blank=True)


class RuleProviderDefinition(models.Model):
    app_label = models.CharField(max_length=100, editable=False)
    slug = models.SlugField(max_length=100, unique=True, editable=False)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = ' Providers/Rule Provider'
        verbose_name_plural = 'Providers/Rules'

    def __str__(self):
        return f'{self.app_label}.{self.slug}'

    def instance(self):
        return engine.rule_providers[self.app_label][self.slug]

    @classmethod
    def get_provider(cls, rule_provider: engine.RuleProviderMixin):
        rule_provider_def, _ = RuleProviderDefinition.objects.get_or_create(
            app_label=rule_provider.app_label(),
            slug=rule_provider.slug()
        )
        return rule_provider_def


class Definition(models.Model):
    rule_provider = models.ForeignKey(RuleProviderDefinition, on_delete=models.CASCADE)
    slug = models.CharField(max_length=100, null=True, blank=True, editable=False,
                            help_text='The item slug that will be used')
    enabled = models.BooleanField(default=True, help_text='If the item is enabled it will be executed')
    registered = models.BooleanField(default=False, editable=False)
    description = models.TextField(max_length=100, null=True, blank=True)

    class Meta:
        abstract = True

    def __str__(self):
        return f'{self.rule_provider}.{self.slug}'

    def eval(self, context, payload, logger):
        ...

    @classmethod
    def register_definition(cls, rule_provider: engine.RuleProviderMixin, definitions: [engine.RuleItem]):
        """
        Register the definitions of a rule provider
        """
        registered = []
        rule_provider_def = RuleProviderDefinition.get_provider(rule_provider)
        for definition in definitions:
            cls.objects.update_or_create(
                rule_provider=rule_provider_def,
                slug=definition.slug,
                defaults=dict(
                    enabled=True,
                    **cls.get_defaults(rule_provider, definition)
                )
            )
            registered.append(definition.slug)

        cls.disabled_not_registered(rule_provider, registered)

    @classmethod
    def get_defaults(cls, rule_provider: engine.RuleProviderMixin, definition: engine.RuleItem):
        return {}

    @classmethod
    def disabled_not_registered(cls, rule_provider: engine.RuleProviderMixin, registered_slugs: [str]):
        """
        Disable all definitions that are not registered in the rule provider
        """
        rule_provider_def = RuleProviderDefinition.get_provider(rule_provider)
        qs = cls.objects.filter(rule_provider=rule_provider_def)
        qs.update(registered=True)
        qs.exclude(slug__in=registered_slugs).update(registered=False)


class ConditionDefinition(Definition):

    class Meta:
        verbose_name = 'Definitions/Condition'
        verbose_name_plural = 'Definitions/Conditions'

    def eval(self, context, payload=None, logger=local_logger):
        provider = self.rule_provider.instance()
        return provider.eval_condition(self.slug, context, payload, logger)

    @classmethod
    def register_conditions(cls, rule_provider: engine.RuleProviderMixin):
        cls.register_definition(rule_provider, rule_provider.conditions())


class ActionDefinition(Definition):
    post_transaction = models.BooleanField(default=False,
                                           editable=False,
                                           help_text='If the action should be executed after the transaction is committed')

    class Meta:
        verbose_name = 'Definitions/Action'
        verbose_name_plural = 'Definitions/Actions'

    def execute(self, context, payload=None, logger=local_logger):
        provider = self.rule_provider.instance()
        return provider.execute(self.slug, context, payload, logger)

    @classmethod
    def register_actions(cls, rule_provider: engine.RuleProviderMixin):
        cls.register_definition(rule_provider, rule_provider.actions())

    @classmethod
    def get_defaults(cls, rule_provider: engine.RuleProviderMixin, definition: engine.RuleItem):
        return dict(post_transaction=cast(ActionDefinition, definition).post_transaction)


class OperantType(models.TextChoices):
    AND = 'AND', 'AND'
    OR = 'OR', 'OR'


class ConditionPosition(models.Model):
    condition = models.ForeignKey(ConditionDefinition, on_delete=models.CASCADE,
                                  related_name='condition_positions')
    rule_definition = models.ForeignKey('RuleDefinition', on_delete=models.CASCADE,
                                        related_name='condition_positions')
    position = models.PositiveIntegerField()


class ActionPosition(models.Model):
    action = models.ForeignKey(ActionDefinition, on_delete=models.CASCADE,
                               related_name='action_positions')
    rule_definition = models.ForeignKey('RuleDefinition', on_delete=models.CASCADE,
                                        related_name='action_positions')
    position = models.PositiveIntegerField()


class RuleDefinition(BaseCoreModel):
    operant = models.CharField(max_length=5,
                               choices=OperantType,
                               default=OperantType.AND,
                               help_text='The operant that will be used to combine the conditions in the rule')

    conditions = models.ManyToManyField(ConditionDefinition,
                                        blank=True,
                                        related_name='rules_definitions',
                                        through=ConditionPosition,
                                        help_text='The conditions that must be met for the rule to be '
                                                  'executed all conditions must be met for the rule to be executed')

    payload = models.ManyToManyField(Payload, blank=True, related_name='rules_definitions')

    actions = models.ManyToManyField(ActionDefinition,
                                     blank=True,
                                     related_name='rules_definitions',
                                     through=ActionPosition,
                                     help_text='The actions that will be executed when the rule is triggered.'
                                               'Run in a transaction.')

    post_transaction_actions = models.ManyToManyField(ActionDefinition,
                                                      blank=True,
                                                      related_name='post_transaction_rules_definitions',
                                                      help_text='Actions that will be executed after the transaction is committed')

    run_on_task = models.BooleanField(default=True, help_text='If the rule should be executed on celery')

    enabled = models.BooleanField(default=True, help_text='If the rule is disabled it will not be executed')

    class Meta:
        verbose_name = 'Definitions/Rule'
        verbose_name_plural = 'Definitions/Rules'

    def eval_conditions(self, context=None, payload=None, logger=local_logger, dry_run=True):
        payload = payload and {**payload} or {}
        for pl in self.payload.all():
            payload.update(pl.payload)

        rule = engine.Rule(
            slug=self.slug,
            operator=engine.LogicalOperator.AND if self.operant == OperantType.AND else engine.LogicalOperator.OR,
            conditions=self.conditions.all().order_by('condition_positions__position')
        )
        rule.eval_conditions(context, payload, logger, dry_run)

    def eval_actions(self, context=None, payload=None, logger=local_logger, dry_run=True):
        payload = payload and {**payload} or {}
        for pl in self.payload.all():
            payload.update(pl.payload)

        rule = engine.Rule(
            slug=self.slug,
            actions=self.actions.all().order_by('action_positions__position'),
            post_transaction_actions=self.post_transaction_actions.all()
        )
        rule.eval_actions(context, payload, logger, dry_run)

    def eval(self, context=None, payload=None, logger=local_logger, dry_run=True, running_on_task=False):
        """
        """
        if self.enabled:
            if not running_on_task and not dry_run and self.run_on_task:
                tasks.eval_rule.delay(self.id)
                logger.info(f'Rule {self.slug} will be executed on task')
                return

            rule = engine.Rule(
                slug=self.slug,
                operator=engine.LogicalOperator.AND if self.operant == OperantType.AND else engine.LogicalOperator.OR,
                conditions=self.conditions.all().order_by('condition_positions__position'),
                actions=self.actions.all().order_by('action_positions__position'),
                post_transaction_actions=self.post_transaction_actions.all()
            )
            return rule.eval(context, payload, logger, dry_run)
        else:
            logger.info(f'Rule {self.slug} is disabled')

    def to_mermaid(self):
        """
        Returns the mermaid representation of the rule
        """
        builder = FlowchartBuilder(title=self.slug)
        if self.run_on_task:
            builder.create_edge('task', link_label='run on task')

        for condition in self.conditions.all():
            builder.push_condition(condition.slug)

        for action in self.actions.all():
            builder.create_edge(action.slug)

        return builder.flowchart


registered_signals = {}


class RuleModelSignal(Tracking):

    when = models.CharField(max_length=100, choices=SignalChoices.choices, unique=True,
                            help_text='The signals that will trigger the rule')

    content_type = models.ForeignKey(ContentType,
                                     related_name='rule_signals',
                                     on_delete=models.CASCADE,
                                     help_text='The content type that triggered the rule')

    rules = models.ManyToManyField(RuleDefinition, related_name='signals',
                                   help_text='The rules that will be triggered by the signal')

    description = models.TextField(max_length=100, null=True, blank=True)

    last_executed = models.DateTimeField(null=True, blank=True, editable=False)
    last_registered = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        verbose_name = 'Triggers/Model Signal'
        verbose_name_plural = 'Triggers/Model Signals'
        unique_together = ('when', 'content_type')

    def __str__(self):
        return f'{self.when}({self.content_type}) -> rules'

    def to_mermaid(self):
        """
        Returns the mermaid representation of the rule
        """
        builder = FlowchartBuilder(title=str(self.content_type))
        for rule in self.rules.all():
            builder.add_edge(rule.to_mermaid(), link_label=str(self.when))
        return builder.flowchart

    @classmethod
    def register_signals(cls):
        for rule_signal in cls.objects.all():
            rule_signal_id = rule_signal.id
            if rule_signal_id not in registered_signals:
                model = rule_signal.content_type.model_class()
                rule_signal.last_registered = timezone.now()
                rule_signal.save()

                signal_helper = ModelSignalHelper(name=str(rule_signal), model=model, description=rule_signal.description)
                registered_signals[rule_signal_id] = signal_helper
                signal_helper.listen(rule_signal.when, rule_signal.wrap_callback())
                signal_helper.connect()

    def wrap_callback(self):
        my_id = self.id

        def callback(*args, **kwargs):
            self.callback(my_id, args, kwargs)
        return callback

    @classmethod
    def callback(cls, signal_def_id, signal_args, signal_kwargs):
        rule_signal = RuleModelSignal.objects.get(pk=signal_def_id)
        rule_signal.last_executed = timezone.now()
        rule_signal.save()

        signal = dict(
            sender=signal_kwargs['sender'],
            instance=signal_kwargs['instance'],
            args=signal_args,
            kwargs=signal_kwargs,
        )

        context = dict(
            request={},
            instance=signal_kwargs['instance'],
            signal=signal,
            rule_signal=rule_signal,
        )

        for rule in rule_signal.rules.all():
            try:
                rule.eval(context=context, dry_run=False)
            except Exception:
                local_logger.exception(f'Error executing rule {rule.slug} triggered by signal {rule_signal}')


class RuleExecution(models.Model):
    rule = models.ForeignKey(RuleDefinition, on_delete=models.CASCADE, editable=False,
                             related_name='rule_executions')

    content_type = models.ForeignKey('contenttypes.ContentType',
                                     related_name='rule_executions',
                                     null=True, blank=True,
                                     on_delete=models.CASCADE, editable=False,
                                     help_text='The content type of the instance that triggered the rule')
    instance_id = models.BigIntegerField(editable=False, help_text='The id of the instance that triggered the rule')

    success = models.BooleanField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        verbose_name = 'Executions/Rule '
        verbose_name_plural = 'Executions/Rules'


class ExecutionItem(models.Model):
    rule_execution = models.ForeignKey(RuleExecution, on_delete=models.CASCADE, editable=False)
    success = models.BooleanField(editable=False)
    debug = models.JSONField(null=True, blank=True, editable=False)
    exception = models.TextField(max_length=1000, null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    class Meta:
        abstract = True


class ConditionExecution(ExecutionItem):

    class Meta:
        verbose_name = 'Executions/Condition '
        verbose_name_plural = 'Executions/Conditions'

    condition = models.ForeignKey(ConditionDefinition, null=True, blank=True, editable=False,
                                  on_delete=models.SET_DEFAULT, default=None,
                                  related_name='condition_executions')


class ActionExecution(ExecutionItem):

    class Meta:
        verbose_name = 'Executions/Action '
        verbose_name_plural = 'Executions/Actions'

    action = models.ForeignKey(ActionDefinition, null=True, blank=True, editable=False,
                               on_delete=models.SET_DEFAULT, default=None,
                               related_name='action_executions')

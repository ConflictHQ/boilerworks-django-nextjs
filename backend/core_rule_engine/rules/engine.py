import dataclasses
import logging
from enum import Enum

from django.db import transaction

local_logger = logging.getLogger(__name__)


class RuleException(Exception):

    def __init__(self, rule, message, fatal=False, debug: dict = None):
        self.rule = rule
        self.message = message
        self.fatal = fatal
        self.debug = debug
        super().__init__(self.message)


@dataclasses.dataclass
class Result:
    success: bool
    debug: dict = None


@dataclasses.dataclass
class RuleItem:
    slug: str
    provider: 'RuleProviderMixin'
    description: str = None

    def required_variables(self) -> [str]:
        return ()


@dataclasses.dataclass
class Condition(RuleItem):

    def eval(self, context, payload, logger) -> bool:
        """
        Note: The condition must not generate side effects
        context: contains the instance of the model that triggered the rule
        return: True if the condition is met, False otherwise or exception if the condition fails
        """
        ...


@dataclasses.dataclass
class Action(RuleItem):
    post_transaction: bool = False

    def execute(self, context, payload, logger) -> None:
        """
        context: contains the instance of the model that triggered the rule
        return: debug: None or dict with debug information or throw an exception if the action fails

        if post_transaction is true this, will be executed after the transaction is committed.
            Example: Send an email
            This actions must not modify the database
        """
        ...


@dataclasses.dataclass
class RuleProviderMixin:
    """
    Optional:
        Eval and Do will check if the there is a method with the slug name
        If there is a method with the slug name it will be executed. It must receive the context and the payload
    """
    conditions_dict: dict = dataclasses.field(default_factory=dict)
    actions_dict: dict = dataclasses.field(default_factory=dict)

    def app_label(self) -> str:
        """
        Returns the app label of the rule provider
        """
        ...

    def slug(self) -> str:
        """
        Returns the slug of the rule provider
        """
        ...

    def _add(self, conditions: [Condition], actions: [Action]):
        for condition in conditions:
            self.conditions_dict[condition.slug] = condition

        for action in actions:
            self.actions_dict[action.slug] = action

    def conditions(self) -> [Condition]:
        return self.conditions_dict.values()

    def actions(self) -> [Action]:
        return self.actions_dict.values()

    def get_condition(self, slug) -> [Condition | None]:
        return self.conditions_dict.get(slug)

    def get_action(self, slug) -> [Condition | None]:
        return self.actions_dict.get(slug)

    def eval_condition(self, slug, context, payload, logger) -> bool:
        condition = self.get_condition(slug)
        if condition:
            return condition.eval(context, payload, logger)
        else:
            raise RuleException(self, f'Condition {self.slug} not found in provider {self.slug()}', fatal=True)

    def execute(self, slug, context, payload, logger) -> Result:
        action = self.get_action(slug)
        if action:
            return action.execute(context, payload, logger)


class LogicalOperator(Enum):
    AND = 'AND'
    OR = 'OR'


@dataclasses.dataclass
class Rule:
    slug: str
    operator: LogicalOperator = LogicalOperator.AND
    conditions: [Condition] = dataclasses.field(default_factory=list)
    actions: [Action] = dataclasses.field(default_factory=list)
    post_transaction_actions: [Action] = dataclasses.field(default_factory=list)

    def eval(self, context=None, payload=None, logger=local_logger, dry_run=True):
        if self.eval_conditions(context, payload, logger, dry_run):
            self.eval_actions(context, payload, logger, dry_run)

    def eval_conditions(self, context=None, payload=None, logger=local_logger, dry_run=True):
        if not self.conditions:
            logger.info('No conditions defined. Rule met')
            return True

        context = self._create_context(context, dry_run=dry_run)

        logger.info('Evaluating conditions:')
        for condition in self.conditions:
            child_logger = logger.getChild(f'{condition.slug}')
            result = condition.eval(context, payload, child_logger)
            child_logger.debug(f'Condition {condition.slug} result: {result}')
            if self.operator == LogicalOperator.AND:
                if not result:
                    child_logger.info(f'AND Condition {condition.slug} result: {result}. Evaluation stopped')
                    return False
            elif result:
                child_logger.debug('OR Evaluation stopped')
                break
            else:
                child_logger.debug('OR Evaluation continue')

        logger.info('Condition met')
        return True

    def eval_actions(self, context=None, payload=None, logger=local_logger, dry_run=True):
        try:
            with transaction.atomic():
                transaction.on_commit(lambda: self._eval_post_transaction_actions(context, payload, logger, dry_run))
                self._eval_actions(self.actions, context, payload, logger, dry_run=dry_run)
                if dry_run:
                    self._eval_post_transaction_actions(context, payload, logger, dry_run)
                    logger.info('Dry run: Rolling back transaction')
                    transaction.set_rollback(True)
        except Exception as e:
            logger.exception('Error executing actions')
            raise e

    @classmethod
    def _create_context(cls, context, dry_run=True, post_transaction=False):
        context = context and {**context} or {}
        context['dry_run'] = dry_run
        context['post_transaction'] = post_transaction
        return context

    def _eval_actions(self, actions, context, payload, logger, dry_run=True, post_transaction=False):
        context = self._create_context(context, dry_run=dry_run, post_transaction=post_transaction)

        transaction_str = post_transaction and 'post transaction' or 'in transaction'
        if not len(actions):
            logger.info(f'No {transaction_str} actions defined')
            return

        logger.info(f'Executing {transaction_str} actions:')

        for action in actions:
            try:
                action.execute(context, payload, logger.getChild(f'{action.slug}'))
            except Exception as e:
                if post_transaction:
                    logger.exception(f'Error executing post transaction action {action.slug}')
                else:
                    raise RuleException(self, f'Error executing action {action.slug}', debug={'exception': e})

    def _eval_post_transaction_actions(self, context, payload, logger, dry_run=True):
        self._eval_actions(self.post_transaction_actions, context, payload, logger, dry_run=dry_run, post_transaction=True)


rule_providers = {}


def register_rule_provider(rule_provider: RuleProviderMixin):
    """
    Register a rule provider
    """
    from core_rule_engine.models import ActionDefinition, ConditionDefinition

    if rule_provider.app_label() not in rule_providers:
        rule_providers[rule_provider.app_label()] = {}

    rule_providers[rule_provider.app_label()][rule_provider.slug()] = rule_provider

    ConditionDefinition.register_conditions(rule_provider)
    ActionDefinition.register_actions(rule_provider)

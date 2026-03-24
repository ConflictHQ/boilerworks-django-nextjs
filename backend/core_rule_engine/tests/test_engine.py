import dataclasses
import unittest
from unittest.mock import MagicMock, patch

from core.tests.utils.base_test import BaseTest
from core.utils.logger_helper import InMemoryLogHandler
from core_rule_engine.common_rule_items import ConditionFalsy, ConditionTruthy, HelloWorldAction
from core_rule_engine.rules import engine
from core_rule_engine.rules.engine import LogicalOperator, Rule, RuleException
from freezegun import freeze_time


@dataclasses.dataclass
class BrokenAction(engine.Action):
    """
    ConditionTruthy
    """
    def __init__(self, *args, **kwargs):
        super().__init__(slug='Broken', *args, **kwargs)

    def execute(self, context, payload, logger):
        raise RuleException(None, 'Action failed')


@freeze_time("2023-10-28T00:00:00+00:00")
class TestRule(BaseTest):

    def setUp(self):
        # Setup mock logger
        self.logger = InMemoryLogHandler.get_logger('test_logger', propagate=True)

        # Setup mock context and payload
        self.context = {'some': 'context', 'now': "2023-10-28T00:00:00+00:00"}
        self.payload = {'data': 'payload'}

        self.true_condition = ConditionTruthy(provider=self)
        self.false_condition = ConditionFalsy(provider=self)
        self.action = HelloWorldAction(provider=self)

    def before_each(self):
        self.logger = InMemoryLogHandler.get_logger('test_logger', propagate=True)

    @patch('django.db.transaction.atomic', new_callable=MagicMock)
    @patch('django.db.transaction.on_commit', new_callable=MagicMock)
    def test_eval_conditions_and_operator_all_true(self, mock_atomic, mock_on_commit):
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.AND,
            conditions=[self.true_condition, self.true_condition],
            actions=[self.action]
        )

        result = rule.eval_conditions(self.context, self.payload, self.logger)

        self.assertTrue(result)

    def test_eval_conditions_and_operator_one_false(self):
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.AND,
            conditions=[self.true_condition, self.false_condition],
            actions=[self.action]
        )

        result = rule.eval_conditions(self.context, self.payload, self.logger)
        self.assertFalse(result)

    def test_eval_conditions_or_operator(self):
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.OR,
            conditions=[self.false_condition, self.true_condition],
            actions=[self.action]
        )

        result = rule.eval_conditions(self.context, self.payload, self.logger)
        self.assertTrue(result)

    @patch('django.db.transaction.atomic', new_callable=MagicMock)
    @patch('django.db.transaction.on_commit', new_callable=MagicMock)
    def test_eval_actions_dry_run(self, mock_atomic, mock_on_commit):
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.AND,
            actions=[self.action]
        )

        rule.eval_actions(self.context, self.payload, self.logger, dry_run=True)
        self.assertMatchSnapshot(self.logger.handlers[0].to_html())

    def test_raise_exception_if_action_fails(self):
        # Setup action to raise an exception
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.AND,
            actions=[BrokenAction(provider=self)]
        )

        with self.assertRaises(RuleException):
            rule.eval_actions(self.context, self.payload, self.logger, dry_run=False)

    def test_eval_post_transaction_actions(self):
        rule = Rule(
            slug="test_rule",
            operator=LogicalOperator.AND,
            post_transaction_actions=[self.action]
        )

        with patch('django.db.transaction.on_commit', new_callable=MagicMock):
            rule._eval_post_transaction_actions(self.context, self.payload, self.logger, dry_run=False)
            self.assertMatchSnapshot(self.logger.handlers[0].to_html())


if __name__ == '__main__':
    unittest.main()

"""Integration test for core_rule_engine app registration (issue #110).

The app must be in INSTALLED_APPS (behind FEATURE_RULE_ENGINE), its models
must migrate (test DB creation covers that), and register_rule_providers()
must run against those tables without raising.
"""
from core_rule_engine.common_rule_items import register_rule_providers
from core_rule_engine.models import ActionDefinition, ConditionDefinition, RuleProviderDefinition
from core_rule_engine.rules import engine
from django.apps import apps
from django.test import TestCase


class RuleEngineAppInstalledTest(TestCase):
    """The rule engine is wired into the running app, not dead code."""

    def test_app_is_installed(self):
        self.assertTrue(apps.is_installed('core_rule_engine'))

    def test_register_rule_providers_registers_against_the_database(self):
        """register_rule_providers() persists the common provider and its items."""
        register_rule_providers()

        self.assertIn('core_rule_engine', engine.rule_providers)
        self.assertIn('common', engine.rule_providers['core_rule_engine'])

        provider = RuleProviderDefinition.objects.get(app_label='core_rule_engine', slug='common')
        self.assertTrue(
            ConditionDefinition.objects.filter(rule_provider=provider, slug='truthy', registered=True).exists(),
        )
        self.assertTrue(
            ActionDefinition.objects.filter(rule_provider=provider, slug='hello_world', registered=True).exists(),
        )

import logging

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CoreRuleEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core_rule_engine'

    def ready(self):
        from core_rule_engine.common_rule_items import register_rule_providers
        from core_rule_engine.models import RuleModelSignal

        try:
            register_rule_providers()
            RuleModelSignal.register_signals()
        except Exception as e:
            # Expected before migrations have run (e.g. first boot, test DB creation)
            logger.warning(f'Error registering signals: {e}')

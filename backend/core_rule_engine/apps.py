from django.apps import AppConfig


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
            print(f'Error registering signals: {e}')

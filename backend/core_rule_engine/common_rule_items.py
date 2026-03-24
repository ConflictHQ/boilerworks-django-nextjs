import dataclasses

from core_rule_engine.rules import engine


@dataclasses.dataclass
class ConditionTruthy(engine.Condition):
    """
    ConditionTruthy
    """
    def __init__(self, *args, **kwargs):
        super().__init__(slug='truthy', *args, **kwargs)

    def eval(self, context, payload, logger) -> bool:
        if 'user' in context:
            logger.info(f'User: {context["user"]}')
        else:
            logger.info('No User')
        return True


@dataclasses.dataclass
class ConditionFalsy(engine.Condition):
    """
    ConditionTruthy
    """
    def __init__(self, *args, **kwargs):
        super().__init__(slug='falsy', *args, **kwargs)

    def eval(self, context, payload, logger) -> bool:
        return False


@dataclasses.dataclass
class HelloWorldAction(engine.Action):
    """
    ConditionTruthy
    """
    def __init__(self, *args, **kwargs):
        super().__init__(slug='hello_world', *args, **kwargs)

    def execute(self, context, payload, logger):
        if 'request' in context:
            logger.info(f'Hello World - {context["request"].user}')
        else:
            logger.info(f'Hello World - {context["now"]}')


@dataclasses.dataclass
class CommonRuleProvider(engine.RuleProviderMixin):
    """
    CommonRuleItem
    """
    def app_label(self) -> str:
        return 'core_rule_engine'

    def slug(self) -> str:
        return 'common'

    def __post_init__(self):
        self._add([ConditionTruthy(provider=self)], [HelloWorldAction(provider=self)])


# Register the rule provider
def register_rule_providers():
    engine.register_rule_provider(CommonRuleProvider())

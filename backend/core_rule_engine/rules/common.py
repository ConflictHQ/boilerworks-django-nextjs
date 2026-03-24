import dataclasses
import logging

from durable import lang
from durable.lang import m

from .engine import Rule

logger = logging.getLogger(__name__)


@dataclasses.dataclass
class TodayRule(Rule):
    name = 'Today'

    def register(self):

        with lang.ruleset('today'):
            @lang.when_all(m.subject == 'today')
            def today(c):
                c.satisfy()
        pass

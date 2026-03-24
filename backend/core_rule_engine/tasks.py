
from config.celery import app
from core.utils.logger_helper import InMemoryLogHandler


@app.task()
def eval_rule(rule_id):
    from core_rule_engine.models import RuleDefinition

    rule = RuleDefinition.objects.get(id=rule_id)
    mem_logger = InMemoryLogHandler.get_logger(f'{rule.slug}', propagate=True)
    rule.eval(logger=mem_logger, running_on_task=True)

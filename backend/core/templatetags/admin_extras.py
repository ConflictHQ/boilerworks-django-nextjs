import datetime

from django import template

register = template.Library()

deploy_time = datetime.datetime.now()


@register.simple_tag
def up_time():
    from core.utils.admin import timedelta_to_str

    dt = datetime.datetime.now() - deploy_time
    return timedelta_to_str(dt)

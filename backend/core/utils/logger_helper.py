import json
import logging
from functools import wraps

from django.conf import settings

logger = logging.getLogger(__name__)


def dump_json(query):
    dump = ''
    if 'query' in query:
        i = 1
        for key in ['operationName', 'variables']:
            if key in query:
                dump += f': {key}\n'
                for line in json.dumps(query[key], indent=2).split('\n'):
                    dump += f'{line}\n'

        for line in query['query']:
            dump += f'{i}: {line}\n'
            i += 1
    else:
        for line in json.dumps(query, indent=2).split('\n'):
            dump += f'{line}\n'

    return dump


def gql_logger(view_func):
    """
    Temporal solution for login user.
    """
    """Mark a view function as being exempt from the CSRF view protection."""

    # view_func.csrf_exempt = True would also work, but decorators are nicer
    # if they don't have side effects, so return a new function.
    def wrapped_view(*args, **kwargs):
        query = {}
        if settings.DEBUG:
            try:
                query = json.loads(args[0].body)
                dump = f'>>>---request---------->>> {query["operationName"]}  ------------------------\n'
                variables = '\n      '.join(sorted([f'{n} = {v}' for n, v in query['variables'].items()]))
                dump += f'  query: {query["operationName"]} \n    variables:\n      {variables}\n'
                logger.warning(dump)
            except Exception as e:
                logger.warning('request error', e)

        result = view_func(*args, **kwargs)

        if settings.DEBUG:
            try:
                response = json.loads(result.content)
                dump = f'  ---response-----------  {query["operationName"]}  -------------------------\n'
                if 'errors' in response:
                    dump += dump_json(response)
                    if hasattr(args[0], 'django_debug'):
                        for e in args[0].django_debug.object.exceptions:
                            dump += f'    {e.stack}\n'
                else:
                    dump += '    response ok\n'
                dump += f'<<<---end request-------<<< {query["operationName"]} --------------------\n'
                logger.warning(dump)
            except Exception as e:
                logger.warning('request ', e)

        return result

    return wraps(view_func)(wrapped_view)


class InMemoryLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_records = []  # Store log records in a list

    def emit(self, record):
        log_entry = self.format(record)  # Format the record as a string
        self.log_records.append(log_entry)  # Append to the list

    def get_logs(self):
        return self.log_records

    def clear_logs(self):
        self.log_records.clear()

    def to_string(self):
        return '\n'.join(self.log_records)

    def to_html(self):
        return '<br/>'.join(self.log_records)

    @classmethod
    def get_logger(cls, name, propagate=False):
        mem_logger = logging.getLogger(name)
        mem_logger.setLevel(logging.DEBUG)
        mem_logger.propagate = propagate

        if mem_logger.hasHandlers():
            mem_logger.handlers.clear()

        handler = InMemoryLogHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M')
        handler.setFormatter(formatter)
        mem_logger.addHandler(handler)
        return mem_logger

import logging
import traceback
from typing import List

from graphql import GraphQLError

logger = logging.getLogger(__name__)


def errors_to_str(errors: List[GraphQLError | Exception] | GraphQLError | Exception):
    if not isinstance(errors, list):
        errors = [errors]

    stacks = []
    for error in errors:
        try:
            while hasattr(error, 'original_error'):
                if error.original_error is None:
                    break
                error = error.original_error
            traceback.print_exception(type(error), error, error.__traceback__)
            stack_trace_str = traceback.format_exception(type(error), error, error.__traceback__)

            return ''.join(stack_trace_str)
        except AttributeError as exc:
            logger.error(f'Object of type {type(exc)} has no attribute original error')
            return str(error)

    return '\n'.join(stacks)

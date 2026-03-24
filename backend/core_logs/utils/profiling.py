import time
from functools import wraps

from django.core.handlers.wsgi import WSGIRequest


class RecordProfiling:

    def __init__(self, func_name, args=None, kwargs=None):
        self.func_name = func_name
        self.children = []
        self.args = args
        self.kwargs = kwargs


class RequestProfiling:

    def __init__(self):
        self.call_stack = [RecordProfiling('root')]

    def push(self, func_name, args=None, kwargs=None):
        new_record = RecordProfiling(func_name, args, kwargs)
        self.call_stack[-1].children.append(new_record)
        self.call_stack.append(new_record)

    def pop(self, duration):
        record = self.call_stack.pop()
        record.duration = duration


def request_profiling(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request = find_request(args) or find_request(kwargs)
        if request:
            if not hasattr(request, 'profiling'):
                request.profiling = RequestProfiling()
            request.profiling.push(func.__name__)

        start_time = time.time()  # Capture the start time
        result = func(*args, **kwargs)  # Call the function
        if request:
            end_time = time.time()
            request.profiling.pop(end_time - start_time)

        return result
    return wrapper


def find_request(args):
    args = args.values() if isinstance(args, dict) else args
    for arg in args:
        if isinstance(arg, WSGIRequest):
            return arg
        if hasattr(arg, 'request') and isinstance(arg.request, WSGIRequest):
            return arg.request
        if hasattr(arg, 'context') and isinstance(arg.context, WSGIRequest):
            return arg.context
    return None

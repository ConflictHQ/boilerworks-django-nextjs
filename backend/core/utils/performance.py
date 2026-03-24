import logging
import random
from datetime import timedelta
from functools import wraps

from django.core.cache import caches

logger = logging.getLogger(__name__)


def serializer_deserializer(store: bool, data):
    return data


def cache_class_method(timeout=timedelta(seconds=1),
                       key_gen=None,
                       serializer=serializer_deserializer,
                       cache_name='default'):
    cache = caches[cache_name]

    def decorator(method):
        @wraps(method)
        def wrapper(*args, **kwargs):
            # Generate a unique cache key based on the class name, method name, and arguments
            if key_gen:
                key_args = key_gen(*args, **kwargs)
            else:
                key_args = f"{hash(tuple(args))}_{hash(frozenset(kwargs.items()))}"

            key = f"{method.__name__}_{key_args}_{id(timeout)}"

            # Try to get the cached result
            try:
                result = cache.get(key)
            except Exception as e:
                logger.warning(f"Error getting cache key {key}: {e}, skipping cache")
                return method(*args, **kwargs)

            if result is None:
                result = method(*args, **kwargs)
                cache.set(key, serializer(True, result), timeout.seconds + random.randint(0, int(timeout.seconds*0.1)))
            else:
                result = serializer(False, result)
            return result
        return wrapper
    return decorator


def vmprof_profile(output_file='profile_output.vmprof', period=0.01, memory=True):
    # before use this decorator you need to install vmprof
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Open the file to get a file descriptor
            with open(output_file, 'wb+') as f:
                fd = f.fileno()  # Get the file descriptor
                import vmprof
                vmprof.enable(fd, period=period, memory=memory)

                try:
                    # Execute the decorated function
                    result = func(*args, **kwargs)
                finally:
                    # Stop profiling
                    vmprof.disable()

            return result
        return wrapper
    return decorator

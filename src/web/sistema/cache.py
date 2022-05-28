# Quick fix to possibly survive high QPS
# TODO: refactor from here
from hashlib import sha1
from django.core.cache import cache as _djcache


def cache(seconds=900):
    """
    Cache the result of a function call for the specified number of seconds,
    using Django's caching mechanism.
    Assumes that the function never returns None (as the cache returns None to indicate a miss), and that the function's result only depends on its parameters.
    Note that the ordering of parameters is important. e.g. myFunction(x = 1, y = 2), myFunction(y = 2, x = 1), and myFunction(1,2) will each be cached separately.

    Usage:

    @cache(600)
    def myExpensiveMethod(parm1, parm2, parm3):
        ....
        return expensiveResult
    """
    def doCache(f):
        def x(*args, **kwargs):
            arg_names = [str(arg.id) if hasattr(arg, 'id') else str(arg) for arg in args]
            kwarg_names = [
                f"{name}={value.id if hasattr(value, 'id') else str(value)}"
                for name, value in kwargs.items()
            ]
            key_name = f"{f.__module__}.{f.__name__}({';!;'.join(arg_names)};!!;{';!;'.join(kwarg_names)})"
            key = sha1(key_name.encode('utf-8')).hexdigest()
            cache_value = _djcache.get(key)
            if cache_value is None:
                result = f(*args, **kwargs)
                _djcache.set(key, (True, result), seconds)
            else:
                _, result = cache_value
            return result
        return x
    return doCache
# TODO: to here

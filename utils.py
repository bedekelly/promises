"""
utils.py

Miscellaneous utilities that aren't particularly specific to the project's
core capabilities.
"""

from functools import wraps


def optional_args(decorator):
    """
    Define a meta-decorator to describe a decorator which can, optionally,
    take keyword arguments. The following are both valid with this decorator:

    @promise
    def fn():
        ...

    @promise(verbose=True)
    def fn():
        ...

    :param decorator: The decorator to meta-ify.
    :return: The modified decorator.
    """
    @wraps(decorator)
    def new_decorator(*args, **kwargs):
        # Assumption: a single callable argument implies that we're decorating
        # a function. Optional *keyword* arguments are recommended.
        if len(args) == 1 and callable(args[0]):
            return decorator(args[0])
        return lambda fn: decorator(fn, **kwargs)
    return new_decorator

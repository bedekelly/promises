from collections import namedtuple
from threading import Thread

ChainItem = namedtuple("ChainItem", "expected on_match otherwise")
FunctionCall = namedtuple("FunctionCall", "fn args kwargs")


class _Promise:
    """The *actual* promise implementation"""

    def __init__(self, fn, *args, **kwargs):
        self.first_call = FunctionCall(fn, args, kwargs)
        self.call_chain = []

    def on(self, expected, on_match, otherwise=None):
        """
        Add handler functions for the promise we're wrapping.
        :param expected: The value we're checking for.
        :param on_match: A callable to run if the result matches 'expected'.
        :param otherwise: A callable to run if it doesn't.
        """
        self.call_chain.append(ChainItem(expected, on_match, otherwise))
        return self

    def go(self):
        """
        Start the promise chain executing, asynchronously!
        """
        Thread(self.wait).start()

    def wait(self):
        """
        Start the promise chain executing, and wait for the final result!
        """
        # Call the first function given -- the one decorated with @promise.
        fn, args, kwargs = self.first_call
        result = fn(*args, **kwargs)

        # Go through the call chain until we hit a failure, or the end.
        for call_item in self.call_chain:
            expected, on_match, otherwise = call_item
            if result == expected:
                result = on_match(result)
            else:
                return otherwise(result, expected)
        return result


class promise:
    """
    A promise is a way of adding callbacks in a chain that will
    definitely be executed at some point -- we promise!
    """

    def __init__(self, fn):
        self.fn = fn

    def __call__(self, *args, **kwargs):
        """
        Override the raw callable we're decorating to return
        a promise -- that way we can call its `.then` method!
        """
        return _Promise(self.fn, *args, **kwargs)


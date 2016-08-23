from collections import namedtuple
from functools import wraps
from queue import Queue
from threading import Thread

ChainItem = namedtuple("ChainItem", "expected on_match otherwise")
FunctionCall = namedtuple("FunctionCall", "fn args kwargs")


class _Promise:
    """
    The *real* implementation of Promise -- so we can have multiple
    promises starting from the same decorated promise function running at
    once!
    """

    def __init__(self, first_call):
        """
        Create a Promise, given the first function it should call. Also,
        set up the Promise's call chain, and initialise a name for the
        thread which it'll be using to run the `_wait` method.

        :param first_call: The first function in the call chain.
        """
        self.first_call = first_call
        self.call_chain = []
        self._thread = None

    def on(self, expected, on_match, otherwise=None):
        """
        Add an item to the callback chain. This should include an "expected"
        value, a function to call if it matches, and a function to call if
        it doesn't.

        If an `otherwise` function isn't given, use a function which raises
        a ValueError when called.

        :param expected: The value we're checking for.
        :param on_match: A callable to run if the result matches 'expected'.
        :param otherwise: A callable to run if it doesn't.
        """

        def raise_value_error(expected_result, result):
            """The result wasn't what we were expecting; raise a ValueError."""
            raise ValueError("expected({}) does not equal result({})"
                             "".format(expected_result, result))

        if otherwise is None:
            otherwise = raise_value_error

        self.call_chain.append(ChainItem(expected, on_match, otherwise))
        return self

    def go(self):
        """
        Start the promise chain executing, if it's not executing already.
        If it is, don't make a fuss -- just return the promise object as
        usual.
        :returns: The current promise instance, `self`.
        """
        if self._thread is None:
            _thread = Thread(target=self._wait)
            _thread.result_queue = Queue()
            _thread.start()
            self._thread = _thread
        return self

    def wait(self):
        """
        If we've already detached from this Promise and want to reattach
        using `promise.wait()`, just return the result of joining the
        promise thread to the current one. -- i.e. wait for the result.

        If we haven't, we're starting the Promise for the first time.
        Iterate through the call chain, passing results to the next callback
        until we reach either the end, or a failure callback is needed.

        Either way, we return the final result of the callback chain: whether
        that be the return value of the last item in the chain, or the return
        value of the first (and only) failure callback.

        :return: The return value of the last item called in the chain.
        """
        if not self._thread:
            self.go()
        return self._thread.result_queue.get()

    def _return(self, return_value):
        """
        A dummy 'return' statement for the '._wait()' method to use, as the
        `.join()` method of a Thread can't return a value. We place the
        `return value` on a results queue, and in the `.wait()` method we
        can retrieve this same `return_value`.

        :param return_value: The object to place on the result queue.
        :return: The result of placing an item on the queue (not needed).
        """
        return self._thread.result_queue.put(return_value)

    def _wait(self):
        """
        Internal method to iterate through each function in the callback
        chain and pass results from one to the next.
        :return: The result of self._return(...) (not needed).
        """
        # Call the first function given -- the one decorated with @promise.
        fn, args, kwargs = self.first_call
        result = fn(*args, **kwargs)

        # Go through the call chain until we hit a failure, or the end.
        for call_item in self.call_chain:
            expected, on_match, otherwise = call_item
            if result == expected:
                try:
                    result = on_match(result, no_promise=True)
                except TypeError as e:
                    if "unexpected keyword argument" in str(e):
                        result = on_match(result)
                    else:
                        raise
            else:
                return self._return(otherwise(result, expected))
        return self._return(result)


def promise(fn):
    """
    A promise is a way of adding callbacks in a chain that will
    definitely be executed at some point -- we promise!
    """
    @wraps(fn)
    def decorated_function(*args, **kwargs):
        """
        Handle the event when someone calls the function decorated with
        @promise. The first call we make, to kick off the call chain, should
        be this function call -- store it to use later.
        """

        # If we want to just call the wrapped function:
        if kwargs.get("no_promise"):
            del kwargs["no_promise"]
            return fn(*args, **kwargs)

        # Otherwise, treat this as a call to a Promise.
        first_call = FunctionCall(fn, args, kwargs)
        return _Promise(first_call=first_call)

    return decorated_function

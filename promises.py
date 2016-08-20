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
        Create a Promise, given the first function it should call.
        :param first_call: The first function in the call chain.
        """
        self.first_call = first_call
        self.call_chain = []
        self._thread = None

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
        Start the promise chain executing, if it's not executing already.
        If it is, don't make a fuss -- just return the promise object as
        usual.
        """
        if self._thread is None:
            _thread = Thread(target=self._wait)
            _thread.daemon = True
            _thread.start()
            _thread.result_queue = Queue()
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
        """
        if not self._thread:
            self.go()
        return self._thread.result_queue.get()

    def _return(self, retval):
        """
        A dummy 'return' statement for the '_wait' method to use, as the
        .join method of a Thread can't return a value.
        """
        return self._thread.result_queue.put(retval)

    def _wait(self):
        """
        Internal method to iterate through each function in the callback
        chain and pass results from one to the next.
        :return:
        """
        # Call the first function given -- the one decorated with @promise.
        fn, args, kwargs = self.first_call
        result = fn(*args, **kwargs)

        # Go through the call chain until we hit a failure, or the end.
        for call_item in self.call_chain:
            expected, on_match, otherwise = call_item
            if result == expected:
                try:
                    result = on_match(result, inside_promise=True)
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
        if kwargs.get("inside_promise"):
            del kwargs["inside_promise"]
            return fn(*args, **kwargs)
        first_call = FunctionCall(fn, args, kwargs)
        return _Promise(first_call=first_call)
    return decorated_function

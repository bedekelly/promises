import logging
from collections import namedtuple
from functools import wraps
from queue import Queue
from threading import Thread

from utils import optional_args

ChainItem = namedtuple("ChainItem", "expected on_match otherwise")
FunctionCall = namedtuple("FunctionCall", "fn args kwargs")


class _Promise:
    """
    The *real* implementation of Promise -- so we can have multiple
    promises starting from the same decorated promise function running at
    once!
    """

    def __init__(self, first_call, verbose=False):
        """
        Create a Promise, given the first function it should call. Also,
        set up the Promise's call chain, and initialise a name for the
        thread which it'll be using to run the `_wait` method.

        :param first_call: The first function in the call chain.
        """
        self.first_call = first_call
        self.call_chain = []
        self._thread = None
        self.verbose = verbose

    def on(self, expected, on_match, otherwise=None):
        """
        Add an item to the callback chain. This should include an "expected"
        value, an `on_match` function to call if it matches, and an `otherwise`
        function to call if it doesn't.

        If an `otherwise` function isn't given, use a function which raises
        a ValueError when called.

        :param expected: The value we're checking for.
        :param on_match: A callable to run if the result matches 'expected'.
        :param otherwise: A callable to run if it doesn't.
        """

        def raise_value_error(result, expected_result):
            """The result wasn't what we were expecting; raise a ValueError."""
            error = ValueError("expected({}) does not equal result({})"
                               "".format(expected_result, result))
            if self.verbose:
                logging.error(error)
            raise error

        if otherwise is None:
            otherwise = raise_value_error

        self.call_chain.append(ChainItem(expected, on_match, otherwise))
        return self

    def go(self):
        """
        If the promise chain isn't running currently, start it up. This
        method should not block; if a blocking method is required, use the
        `wait()` method.

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
        If we don't have a preexisting thread -- i.e. `.go()` hasn't been
        called yet -- we should start one running.

        Block, and wait for the result of the final callback in the chain;
        this can be either an error-callback, or the final success-callback
        in the chain.

        :return: The return value of the last item called in the chain.
        """
        if not self._thread:
            if self.verbose:
                logging.info("wait() called on promise without preexisting"
                             " thread; starting now...")
            self.go()
        result = self._thread.result_queue.get()
        if self.verbose:
            logging.info("Joining thread...")
        self._thread.join()
        if self.verbose:
            logging.info("Finished thread.")
        return result

    def _return(self, return_value):
        """
        A dummy 'return' statement for the '._wait()' method to use, as the
        `.join()` method of a Thread can't return a value. We place the
        `return value` on a results queue, and retrieve it in the `wait()`
        method.

        :param return_value: The object to place on the result queue.
        :return: The result of placing an item on the queue (not needed).
        """
        return self._thread.result_queue.put(return_value)

    def _wait(self):
        """
        Internal method to iterate through each function in the callback
        chain and pass results from one to the next.

        Todo: refactor exception-handling; this is spaghetti.

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
                except Exception as e:
                    if "unexpected keyword argument" in str(e):
                        try:
                            result = on_match(result)
                        except Exception as e:
                            logging.warning("`on_match` callback raised an "
                                            "exception: ")
                            logging.exception(e)
                            result = e
                            break
                    else:
                        logging.warning("`on_match` callback raised an "
                                        "exception: ")
                        logging.exception(e)
                        result = e
                        break
            else:
                if self.verbose:
                    logging.warning("Result ({}) != Expected ({}) "
                                    "".format(result, expected))
                try:
                    result = otherwise(result, expected)
                except Exception as e:
                    if self.verbose:
                        logging.warning("`otherwise` callback raised an "
                                        "exception: ")
                        logging.exception(e)
                    result = e
                break
        return self._return(result)



@optional_args
def promise(fn, verbose=False):
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
            if verbose:
                logging.info("Bypassing promise mechanism...")
            del kwargs["no_promise"]
            return fn(*args, **kwargs)

        # Otherwise, treat this as a call to a Promise.
        if verbose:
            logging.info("Creating and returning a promise...")
        first_call = FunctionCall(fn, args, kwargs)
        return _Promise(first_call=first_call, verbose=verbose)

    return decorated_function

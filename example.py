import logging
import time

from promises import promise

logging.basicConfig(level=logging.INFO)


def fail(result, expected):
    """Log an error with the given message."""
    logging.warning("Failure in promise: result({}) is not expected({})"
                    "".format(result, expected))
    return result, expected


def add_three(param):
    """Add three to the given parameter."""
    time.sleep(1)
    result = param + 3
    logging.info("Adding three to {}: returning {}".format(param, result))
    return result


@promise
def wait_one(param):
    """Wait a second with the given parameter."""
    logging.info("Waiting for a second with {}...".format(param))
    time.sleep(1)
    return param


(
    wait_one(5)
        .on(5, add_three, otherwise=fail)  # Succeeds,
        .on(8, add_three, otherwise=fail)  # Succeeds,
        .on(9, lambda: None, otherwise=fail)  # Fails!
        .on(10, fail, fail)  # Doesn't get called!
        .wait()
)


logging.info("Creating promise...")
promise_two = wait_one(3)
logging.info("Adding items to callback chain...")
promise_two.on(3, add_three, fail).on(6, wait_one, fail)
logging.info("Starting promise asynchronously...")
promise_two.go()
logging.info("Waiting for promise to join...")
result = promise_two.wait()
logging.info("Got result from promise: {}.".format(result))

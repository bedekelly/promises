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


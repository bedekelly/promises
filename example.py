import logging
import time

from promises import promise

logging.basicConfig(level=logging.INFO)


# HELPER METHODS
# ===============

def fail(promise_result, expected):
    """Log an error with the given message."""
    logging.warning("Failure in promise: result({}) is not expected({})"
                    "".format(promise_result, expected))
    return promise_result, expected


def add_three(param):
    """Add three to the given parameter."""
    time.sleep(1)
    my_result = param + 3
    logging.info("Adding three to {}: returning {}".format(param, my_result))
    return my_result


@promise
def wait_one(param):
    """Wait a second with the given parameter."""
    logging.info("Waiting for a second with {}...".format(param))
    time.sleep(1)
    return param


# USAGE EXAMPLES
# ===============

# Step-by-step:
promise_two = wait_one(3)
promise_two.on(3, add_three, fail)
promise_two.on(6, wait_one, fail)
promise_two.go()
result = promise_two.wait()
logging.info("Got result from promise: {}.".format(result))


# Fluent-API-style:
result = (
    wait_one(5)
        .on(5, add_three, otherwise=fail)  # Succeeds,
        .on(8, add_three, otherwise=fail)  # Succeeds,
        .on(9, add_three)  # Fails!
        .on(12, fail, fail)  # Doesn't get called.
        .wait()
)

logging.info(result)

Promises
=========

A Promise is a way of giving functions callbacks to run, depending on whether
they succeed or fail.

This implementation modifies this slightly -- instead of a single Success or
Failure return type, it provides an "on" method to specify what the return
value should be.

```python
@promise
def add_one(n):
    return n + 1

def success(n):
    print("This function will be called with n: {}".format(n))

def failure(n):
    assert False, "This function won't be called!"

(
    add_one(12)
        .on(13, success, failure)
        .go()
)
```

Promises run asynchronously by default: the `.go()` method doesn't block.

Later on, if you need to retrieve the result of the `success()` or `failure()` method called last, you can run `.wait()` on the promise.

```python
my_promise = add_one(5).go()
print("5+1 is being calculated in the background")
result = my_promise.wait()
assert result == 6
```

(You can also run `.wait()` straight away, and the `.go()` method will be called implicitly.)

```python
result = (
    add_one(5)
        .on(6, add_one, failure)
        .wait()
)

assert result == 7
```

If you've decorated some function with the `@promise` decorator, but don't want to use it as a promise, you can pass the `no_promise` keyword argument in like so:

```python
result = add_one(5, no_promise=True)
assert result == 6
```

Some more example code can be found in [example.py](https://github.com/bedekelly/promises/blob/master/example.py)

Promises
=========

A Promise is a way of giving functions callbacks to run, depending on whether
they succeed or fail.

This implementation modifies this slightly -- instead of a single Success or
Failure return type, it provides an "on" method to specify what the return
type should be.

Some example code can be found in [example.py](https://github.com/bedekelly/promises/blob/master/example.py)
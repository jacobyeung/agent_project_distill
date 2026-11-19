"""Bound each SAM call by the shared deadline; the outer timeout covers native stalls."""
import contextlib
import os
import signal
import time


@contextlib.contextmanager
def call_watchdog(seconds=300):
    deadline = float(os.environ.get('PART2_DEADLINE_MONOTONIC', 'inf'))
    remaining = min(seconds, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError('part 2 hard stop reached')
    def expired(signum, frame):
        raise TimeoutError('SAM 3 call exceeded its remaining budget')
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def bounded(function):
    def wrapped(*args, **kwargs):
        with call_watchdog():
            return function(*args, **kwargs)
    return wrapped

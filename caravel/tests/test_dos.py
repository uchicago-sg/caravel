from google.appengine.api import memcache
from caravel.storage import dos
import time


def test_rate_limit():
    now = 0
    _time, time.time = time.time, lambda: now

    try:
        trace = []
        for i in xrange(5):
            trace.append(dos.rate_limit("key", 3, 60))
        now = 100
        for i in xrange(2):
            trace.append(dos.rate_limit("key", 3, 60))
        assert tuple(trace) == (False, False, False, True, True, False, False)
    finally:
        time.time = _time
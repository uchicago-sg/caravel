from google.appengine.api import memcache
import time
import logging


def current_rate(entity, limit, duration):
    """
    Stores a counter with the given name. This function reports rate limit
    denials based on the given limit.

    >>> current_rate('rlt_test', 2, 60)
    1L
    >>> current_rate('rlt_test', 2, 60)
    2L
    >>> current_rate('rlt_test', 2, 60)
    3L
    """

    key = "ratelimit:{}:{}".format(int(time.time() / duration), entity)
    value = memcache.incr(key, initial_value=0)
    if value > limit:
        logging.info(
            "RateLimitDenied({!r}, value={!r}, limit={!r}, duration={!r})"
            .format(entity, value, limit, duration))
    else:
        logging.info(
            "RateLimitAllowed({!r}, value={!r}, limit={!r}, duration={!r})"
            .format(entity, value, limit, duration))
    return value


def rate_limit(entity, limit, duration=60):
    """
    Runs a rate limit with the given duration.

    >>> rate_limit('rlt_test2', 2)
    False
    >>> rate_limit('rlt_test2', 2)
    False
    >>> rate_limit('rlt_test2', 2)
    True
    """

    return current_rate(entity, limit, duration) > limit

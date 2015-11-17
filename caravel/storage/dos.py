from google.appengine.api import memcache
import time, logging

def rate_limit(entity, limit, duration=60):
    key = "ratelimit:{}:{}".format(int(time.time() / duration), entity)
    value = memcache.incr(key, initial_value=0)
    if value >= limit:
        logging.info(
            "RateLimitDenied({!r}, value={!r}, limit={!r}, duration={!r})"
                .format(entity, value, limit, duration))
    else:
        logging.info(
            "RateLimitAllowed({!r}, value={!r}, limit={!r}, duration={!r})"
                .format(entity, value, limit, duration))
    return value > limit
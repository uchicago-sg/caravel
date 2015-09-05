"""
The cache uses memcached to dramatically reduce the number of database queries.
"""

import functools, logging, json, os
from google.appengine.api import memcache

def cache(function):
    """
    A decorator to add inline caching behavior to a function.
    """

    @functools.wraps(function)
    def inner(*vargs, **kwargs):
        """
        Runs the given function with the cache as a backing.
        """

        # Generate a memcache key from the arguments and function name.
        app_version = os.environ["CURRENT_VERSION_ID"]
        key = json.dumps([app_version, function.__name__, vargs, kwargs])

        # Retrieve from cache.
        serialized = memcache.get(key)
        if serialized:
            result = json.loads(serialized)
            if result:
                return result

        # Generate and write back to cache.
        logging.warning("Cache miss: " + key)
        value = function(*vargs, **kwargs)
        if value:
            memcache.set(key, json.dumps(value), time=3600) # 1 hour
        return value

    def invalidate(*vargs, **kwargs):
        """
        Ensures that the next invocation with these args is not cached.
        """

        # Generate a memcache key from the arguments and function name.
        key = json.dumps([function.__name__, vargs, kwargs])
        memcache.delete(key)

    inner.invalidate = invalidate
    return inner

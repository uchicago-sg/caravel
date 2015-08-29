import models

from google.appengine.api import memcache
from google.appengine.ext import db
import itertools, json, logging

def cached(function):
    """
    A decorator to add inline caching behavior to a function.
    """

    def inner(*vargs, **kwargs):
        """
        Runs the given function with the cache as a backing.
        """

        # Generate a memcache key from the arguments and function name.
        key = json.dumps([function.__name__, vargs, kwargs])

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

@cached
def lookup_listing(permalink):
    """
    Retrieves a listing by permalink.
    """

    ent = models.Listing.get_by_key_name(permalink)
    if not ent:
        return None
    json_dict = db.to_dict(ent)
    json_dict["key"] = permalink
    return json_dict

def invalidate_listing(permalink):
    """
    Marks the cache as having lost the given listing.
    """

    lookup_listing.invalidate(permalink)
    fetch_shard.invalidate("")

@cached
def fetch_shard(shard=""):
    """
    Retrieves the permalinks of all listings to appear on the home page.
    """

    query = models.Listing.all(keys_only=True).order("posting_time")
    return [k.name() for k in query.fetch(30)]

def run_query(query=""):
    """
    Performs a search query over all listings.
    """

    keys = fetch_shard("") # TODO: add actual query handling
    return [lookup_listing(key) for key in keys]

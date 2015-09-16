"""
The cache uses memcached to dramatically reduce the number of database queries.
"""

import functools, logging, json, os, sys
from json import JSONEncoder, JSONDecoder

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.datastore.entity_pb import EntityProto

class DBEncoder(JSONEncoder):
    """Packs an entity as a JSON record."""

    def default(self, obj):
        """Converts an object to a JSON-compatible type."""

        # Pack entities as JSON Objects.
        if isinstance(obj, db.Model):
            record, klass = db.to_dict(obj), obj.__class__
            record["__ent__"] = (klass.__module__, klass.__name__)
            if obj.is_saved():
                record["key_name"] = obj.key().name()
            return record

        return obj

class DBDecoder(JSONDecoder):
    """Unpacks an entity from a JSON record."""

    def __init__(self, *vargs, **kwargs):
        """Initialize this JSONDecoder."""

        super(DBDecoder, self).__init__(
            object_hook=self.object_hook, *vargs, **kwargs)

    def object_hook(self, obj):
        """Parse this object from JSON."""

        # If we have an entity-like dict, unpack it.
        if type(obj) is dict and "__ent__" in obj:
            module, kind = obj["__ent__"]
            del obj["__ent__"]
            klass = getattr(sys.modules[module], kind)
            return klass(**obj)

        return obj

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
            result = DBDecoder().decode(serialized)
            if result:
                return result

        # Generate and write back to cache.
        logging.warning("Cache miss: " + key)
        value = function(*vargs, **kwargs)
        if value:
            memcache.set(key, DBEncoder().encode(value), time=3600) # 1 hour
        return value

    def invalidate(*vargs, **kwargs):
        """
        Ensures that the next invocation with these args is not cached.
        """

        # Generate a memcache key from the arguments and function name.
        app_version = os.environ["CURRENT_VERSION_ID"]
        key = json.dumps([app_version, function.__name__, vargs, kwargs])
        memcache.delete(key)

    inner.invalidate = invalidate
    return inner

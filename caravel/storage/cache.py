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

def cache(func):
    """
    Wraps a regular function as batch cache.
    """

    @batchcache
    @functools.wraps(func)
    def inner(vargs):
        return map(lambda (v, kw): func(*v, **kw), vargs)

    return inner

def batchcache(func):
    """
    A decorator to add inline caching behavior to a function.
    """

    def _key(vargs, kwargs):
        app_version = os.environ["CURRENT_VERSION_ID"]
        return json.dumps([app_version, func.__name__, vargs, kwargs])

    @functools.wraps(func)
    def inner(*vargs, **kwargs):
        """
        Runs the given function with the cache as a backing.
        """

        return batch([(vargs, kwargs)])[0]

    def batch(args):
        """
        Runs this function with the given list of arguments, batching memcache
        elements together.
        """

        # Fetch the existing values from the cache.
        keys = [_key(vargs, kwargs) for vargs, kwargs in args]

        cached = memcache.get_multi(keys)
        writeback = {}
        results = {} 
        arguments = []
        correspondence = []

        # Fill in results that aren't in the cache.
        for key, (vargs, kwargs) in zip(keys, args):
            if key in cached:
                logging.debug("CacheGet({!r}) = {!r}".format(key, cached[key]))
                results[key] = DBDecoder().decode(cached[key])
            else:
                results[key] = None
                correspondence.append(key)
                arguments.append((vargs, kwargs))
                logging.warning("CacheGet({!r}) = (null)".format(key))

        # Fetch remaining elements from the database.
        if arguments:
            for key, result in zip(correspondence, func(arguments)):
                results[key] = result
                if result:
                    writeback[key] = DBEncoder().encode(results[key])
                    logging.debug("CachePut({!r}, {!r})".format(
                        key, writeback[key]))

        # Writeback those elements to memcached.
        if writeback:
            memcache.set_multi(writeback, time=3600)

        return [results[key] for key in keys]

    def invalidate(*vargs, **kwargs):
        """
        Ensures that the next invocation with these args is not cached.
        """

        # Generate a memcache key from the arguments and function name.
        key = _key(vargs, kwargs)
        if memcache.delete(key) == 2:
            logging.info("Invalidating {!r}".format(key))

    inner.invalidate = invalidate
    inner.batch = batch
    
    return inner

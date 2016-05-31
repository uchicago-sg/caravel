from google.appengine.datastore import entity_pb
from google.appengine.api import memcache
from google.appengine.ext import ndb


RTC = "rtc:"
INVALIDATIONS = "stat:inv"
HITS = "stat:hit"
MISSES = "stat:miss"


def ndb_entity_to_protobuf(e):
    """
    Saves an entity to a protobuf.
    """
    if e is None:
        return ""
    return ndb.ModelAdapter().entity_to_pb(e).Encode()


def protobuf_to_ndb_entity(pb):
    """
    Reads an entity from a protobuf.
    """

    # precondition: model class must be imported
    if pb == "":
        return None
    return ndb.ModelAdapter().pb_to_entity(entity_pb.EntityProto(pb))


def invalidate_keys(keys):
    """
    Removes the given entities from memcache.
    """

    memcache.incr(INVALIDATIONS, delta=len(keys), initial_value=0)
    memcache.delete_multi([key.urlsafe() for key in keys], key_prefix=RTC)


def get_keys(keys):
    """
    Fetch and save the given keys into memcache.
    """

    # Perform the first load from memcache.
    urlsafes = [key.urlsafe() for key in keys]
    cache = memcache.get_multi(urlsafes, key_prefix=RTC)
    results = {}

    missing = []
    for urlsafe, key in zip(urlsafes, keys):
        if urlsafe in cache:
            results[key] = protobuf_to_ndb_entity(cache[urlsafe])
        else:
            missing.append(key)

    # Record cache stats.
    memcache.incr(MISSES, delta=len(missing), initial_value=0)
    memcache.incr(HITS, delta=len(results), initial_value=0)

    # Fill anything not yet in cache.
    if missing:
        writeback = {}
        for key, entity in zip(missing, ndb.get_multi(missing)):
            results[key] = entity
            writeback[key.urlsafe()] = ndb_entity_to_protobuf(entity)
        memcache.set_multi(writeback, key_prefix=RTC)

    return [results[key] for key in keys]


def cache_stats():
    """
    Returns a count of the hits, misses, and invalidations of the current day.
    """

    return {
        "invalidations": memcache.get(INVALIDATIONS) or 0,
        "hits": memcache.get(HITS) or 0,
        "misses": memcache.get(MISSES) or 0,
    }

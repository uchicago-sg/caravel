from caravel.storage import entities
from caravel.storage.cache import cache
from google.appengine.ext import db
import heapq

@cache
def lookup_listing(permalink):
    """
    Retrieves a listing by permalink.
    """

    return entities.Listing.get_by_key_name(permalink)

def invalidate_listing(listing):
    """
    Marks the cache as having lost the given listing.
    """

    lookup_listing.invalidate(listing.permalink)
    for keyword in listing.keywords:
        fetch_shard.invalidate(keyword)
    fetch_shard.invalidate("")

@cache
def fetch_shard(shard=""):
    """
    Retrieves the permalinks of all listings to appear on the home page.
    """

    query = entities.Listing.all(keys_only=True).order("-posting_time")
    if shard:
        query = query.filter("keywords =", shard)
    return [k.name() for k in query]

def run_query(query="", offset=0):
    """
    Performs a search query over all listings.
    """

    # Tokenize input query.
    words = query.split()
    if not words:
        words = [""]
    words = words[:5] # TODO: Raise once we know the approximate cost.

    # Retrieve the keys for entities that match all terms.
    shards = [fetch_shard(entities.fold_query_term(w)) for w in words]
    if not shards:
        return # yields empty generator

    # Load each key from all shards lazily.
    def _load(keys):
        while keys:
            # Process listings ten at a time.
            batch, keys = keys[:10], keys[10:]
            listings = lookup_listing.parallel([([b], {}) for b in batch])
            for key, listing in zip(batch, listings):
                if listing and listing.posting_time:
                    yield (listing.posting_time, listing)

    # Merge all shards together via mergesort.
    merged = heapq.merge(*[_load(shard) for shard in shards])
    for _, listing in merged:
        yield listing

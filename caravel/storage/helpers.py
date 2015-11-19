from caravel.storage import entities
from caravel.storage.cache import cache, batchcache
from google.appengine.ext import db
import heapq
import logging


@batchcache
def lookup_listing(args=[]):
    """
    Retrieves many listings by permalink.
    """

    keys = [db.Key.from_path("Listing", v[0]) for (v, kw) in args]
    records = entities.Listing.get(keys)

    for record in records:
        if record:
            record.migrate()

    logging.debug("Lookup({!r}) = {!r}".format(keys, records))

    return records


def invalidate_listing(listing):
    """
    Marks the cache as having lost the given listing.
    """

    lookup_listing.invalidate(listing.permalink)
    for keyword in listing.keywords:
        fetch_shard.invalidate(keyword)
    fetch_shard.invalidate("")


@cache
def fetch_shard(shard):
    """
    Retrieves the permalinks of all listings to appear on the home page.
    """

    query = entities.Listing.all(keys_only=True).order("-posting_time")
    if shard:
        query = query.filter("keywords =", shard)
    keys = [k.name() for k in query.fetch(1000)]
    logging.debug("FetchShard({!r}) = {!r}".format(shard, keys))
    return keys


def run_query(query="", offset=0, length=24):
    """
    Performs a search query over all listings.
    """

    # Tokenize input query.
    words = [entities.fold_query_term(w) for w in query.split()]
    words = [w for w in words if w]
    if not words:
        words = [""]

    # Retrieve the keys for entities that match all terms.
    shards = [fetch_shard(word) for word in words]

    # Extract all elements from each shard.
    all_shards = set(shards[0])
    for shard in shards[1:]:
        all_shards = all_shards & set(shard)
    in_order = [x for x in shards[0] if x in all_shards]

    # Load all listings matching these keys.
    keys = in_order[offset:offset + length]
    listings = lookup_listing.batch([([key], {}) for key in keys])

    # Filter out old or invalid listings.
    results = []
    for listing in listings:
        if not listing or not listing.posting_time:
            continue
        if any([word and word not in listing.keywords for word in words]):
            continue
        results.append(listing)
    return results


def add_inqury(listing, buyer, message):
    """
    Tracks when a given buyer displays interest in the given listing.
    """

    key = listing.key()

    @db.run_in_transaction
    def txn():
        listing = entities.Listing.get(key)
        if buyer not in listing.buyers:
            listing.buyers.append(buyer)
        listing.put()

    invalidate_listing(listing)

from caravel.storage import entities
from caravel.storage.cache import cache
from google.appengine.ext import db

@cache
def lookup_listing(permalink):
    """
    Retrieves a listing by permalink.
    """

    ent = entities.Listing.get_by_key_name(permalink)
    if not ent:
        return None
    json_dict = db.to_dict(ent)
    json_dict["key"] = permalink
    json_dict["photo_urls"] = ent.photo_urls # FIXME: handle getters better

    # FIXME: remove below once all listings are migrated to new schema
    if not json_dict.get("title"):
        json_dict["title"] = json_dict.get("description")
    if not json_dict.get("body"):
        json_dict["body"] = json_dict.get("details")

    return json_dict

def invalidate_listing(permalink, keywords=[]):
    """
    Marks the cache as having lost the given listing.
    """

    lookup_listing.invalidate(permalink)
    for keyword in keywords:
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
    return [k.name() for k in query.fetch(30)]

def run_query(query=""):
    """
    Performs a search query over all listings.
    """

    # Tokenize input query.
    words = query.split()
    if not words:
        words = [""]
    words = words[:5] # TODO: Raise once we know the approximate cost.

    # Retrieve the keys for entities that match all terms.
    shards = [set(fetch_shard(word)) for word in words]
    if not shards:
        return []
    keys = shards[0].intersection(*shards[1:])

    # Find the listings for those keys.
    listings = [lookup_listing(key) for key in keys]
    listings.sort(key=lambda x: -x["posting_time"])

    return listing

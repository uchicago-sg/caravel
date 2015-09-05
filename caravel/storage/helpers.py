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
    return json_dict

def invalidate_listing(permalink):
    """
    Marks the cache as having lost the given listing.
    """

    lookup_listing.invalidate(permalink)
    fetch_shard.invalidate("")

@cache
def fetch_shard(shard=""):
    """
    Retrieves the permalinks of all listings to appear on the home page.
    """

    query = entities.Listing.all(keys_only=True).order("-posting_time")
    return [k.name() for k in query.fetch(30)]

def run_query(query=""):
    """
    Performs a search query over all listings.
    """

    keys = fetch_shard("") # TODO: add actual query handling
    return [lookup_listing(key) for key in keys]

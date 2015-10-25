"""
The migration daemon pulls the latest listings from the old site.
"""

from google.appengine.ext import db

from caravel.storage import entities, helpers
from caravel import app

@app.route("/_internal/migrate_schema")
def migrate_schema():
    q = entities.Listing.all()
    q = q.filter("version <", entities.Listing.SCHEMA_VERSION)

    for listing in q.fetch(100):
        db.transaction(lambda: (listing.migrate(), listing.put()))
        helpers.invalidate_listing(listing.permalink, listing.keywords)

    # Invalidate the cache.
    helpers.invalidate_listing(listing)

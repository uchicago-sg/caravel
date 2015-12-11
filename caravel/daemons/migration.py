"""
The migration daemon pulls the latest listings from the old site.
"""

from caravel import app, model

@app.route("/_internal/migrate_schema")
def migrate_schema():
    q = model.Listing.query(
        model.Listing.version < model.Listing.SCHEMA_VERSION)

    q.map(lambda listing: listing.put(), limit=100)

    return "ok"

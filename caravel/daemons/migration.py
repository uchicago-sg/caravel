"""
The migration daemon pulls the latest listings from the old site.
"""

from google.appengine.ext import ndb
from caravel import app, model
import itertools


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


@app.route("/_internal/migrate_schema")
def migrate_schema():
    q = model.Listing.query(
        model.Listing.version < model.Listing.SCHEMA_VERSION)

    for entities in grouper(itertools.islice(q, 0, 1000), 100):
        ndb.put_multi([entity for entity in entities if entity])

    return "ok"

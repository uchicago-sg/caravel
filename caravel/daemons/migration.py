"""
The migration daemon pulls the latest listings from the old site.
"""

from google.appengine.ext import ndb
from caravel import app, model
import itertools
import datetime
from google.appengine.api import users


def grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.izip_longest(fillvalue=fillvalue, *args)


@app.route("/_internal/migrate_schema")
def migrate_schema():
    horizon = datetime.datetime.now() - model.Listing.MARK_AS_OLD_AFTER

    q = model.Listing.query(
        (model.Listing.version < model.Listing.SCHEMA_VERSION) or
        (model.Listing.posted_at <= horizon and
         model.Listing.keywords >= ""))

    for entities in grouper(itertools.islice(q, 0, 1000), 100):
        ndb.put_multi([entity for entity in entities if entity])

    return "ok"

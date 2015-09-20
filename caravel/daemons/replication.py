"""
The replication daemon pulls the latest listings from the old site.
"""

import json, time, datetime, re, urllib2
from flask import request
from caravel import app
from caravel.storage import entities, helpers
from google.appengine.ext import deferred
from google.appengine.api import taskqueue, urlfetch

@app.route("/_pull", methods=["GET"])
def pull_from_legacy_site():
    """A webhook triggered by the old site that pulls that site."""
    deferred.defer(
        pull_from_old_marketplace,
        permalink=request.args.get("permalink", ""),
        _retry_options=taskqueue.TaskRetryOptions(task_retry_limit=5)
    ) # need to defer to prevent the prod site from deadlocking
    return "ok"

def pull_from_old_marketplace(permalink, _urlopen=urllib2.urlopen):
    """
    Retrieves the listing from the old Marketplace, and save it to the database.
    """

    urlfetch.set_default_fetch_deadline(30)

    # Retrieve existing listing by the permalink.
    if not re.match(r"^[a-zA-Z\-0-9]+$", permalink):
        raise ValueError("Invalid permalink: {!r}".format(permalink))
    url = "http://marketplace.uchicago.edu/{}".format(permalink)
    data = _urlopen(url + ".json").read()
    if not data:
        return

    try:
        json_data = json.loads(data)
    except ValueError, e:
        return

    # Parse the listing date from not-quite-ISO8601 to App Engine UTC.
    posting_time = time.mktime((datetime.datetime.strptime(
        json_data["renewed_at"][:-6], "%Y-%m-%dT%H:%M:%S"
    ) - datetime.timedelta(
        hours=float(json_data["renewed_at"][-6:-3]),
        minutes=float(json_data["renewed_at"][-2:])
    )).timetuple())

    # Remove HTML tags from body.
    cleaned_body = re.sub(r'<[^>]+>', '', json_data["details"])

    # Prepare a listing to update.
    listing = entities.Listing(
        key_name=json_data["permalink"],
        seller=json_data["seller"]["email"],
        posting_time=posting_time,
        title=json_data["description"],
        body=cleaned_body,
        price=(int(float(json_data["price"]) * 100))
    )

    # Download all original photos for this listing.
    html = _urlopen(url).read()
    images = re.finditer(r"<a class='fancybox-image' href='([^']*)'", html)
    prefix = "http://marketplace.uchicago.edu"

    listing.photo_urls = [_urlopen(prefix + m.group(1)) for m in images]

    # (Idempotently) save this entity into the datastore.
    listing.put()

    # Invalidate the cache.
    helpers.invalidate_listing(permalink, listing.keywords)
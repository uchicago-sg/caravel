"""
Listings are placed by sellers when they want to sell things.
"""

import uuid, time, calendar

from flask import render_template, request, abort, redirect, url_for, session
from flask import flash, g, jsonify

from caravel import app, model
from caravel.storage import dos

def _externalize(listing):
    """Returns a safe JSON blob representing the given listing."""

    return {
        "jsonURL": url_for(
            "api_one_listing", listing=listing, _external=True),
        "htmlURL": url_for(
            "show_listing", listing=listing, _external=True),
        "title": listing.title,
        "body": listing.body,
        "postingTime": calendar.timegm(listing.posted_at.timetuple()),
        "categories": [
            {
                "name": category,
                "URL": url_for("api_all_listings",
                    q="category:{}".format(category), _external=True)
            } for category in listing.categories
        ],
        "price": listing.price,
        "photos": [
            {
                "small": photo.public_url("small"),
                "large": photo.public_url("large")
            } for photo in listing.photos
        ]
    }

@app.route("/api")
@app.route("/api/v1")
def api_docs():
    """Bounce user to the documentation Doc."""
    return redirect("https://docs.google.com/document/d/"
                    "1uHTq_U0_v97KuHV1LElDp3hNwrcykaPrk61kT2Igti4/edit")

@app.route("/api/v1/listings.json")
def api_all_listings():
    """Display a list of listings that match the given query."""

    # Parse filtering options from query.
    query = request.args.get("q", "")
    offset = int(request.args.get("offset", "0"))
    if offset < 0:
        offset = 0

    limit = int(request.args.get("limit", "100"))
    if limit < 0:
        limit = 0
    if limit > 100:
        limit = 100

    # Provide a burst limit on search queries.
    if dos.rate_limit("api_search:{}".format(request.remote_addr), 40, 60):
        abort(403)

    # Compute the results matching that query.
    listings = list(model.Listing.matching(query))[offset:offset + limit]

    # Display only whitelisted properties as JSON.
    externalized = [_externalize(listing) for listing in listings]

    pages = {}
    if len(listings) == limit:
        pages["nextURL"] = url_for("api_all_listings",
            offset=offset + limit, _external=True)
    if offset != 0:
        pages["previousURL"] = url_for("api_all_listings",
            offset=max(0, offset - limit), _external=True)

    # Return JSON if requested.
    return jsonify(
        offset=offset,
        listings=externalized,
        limit=limit,
        **pages
    )

@app.route("/api/v1/<listing:listing>.json")
def api_one_listing(listing):
    """Display a single listing matching the given query."""

    # Return JSON if requested.
    return jsonify(_externalize(listing))
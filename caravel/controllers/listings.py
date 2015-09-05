"""
Listings are placed by sellers when they want to sell things.
"""

from caravel import app
from caravel.storage import helpers
from flask import render_template, request, abort

@app.route("/")
def index():
    """Display a list of listings that match the given query."""
    listings = helpers.run_query(request.args.get("q"))
    return render_template("index.html", listings=listings)

@app.route("/<permalink>")
def show(permalink):
    """View a particular listing and provide links to place an inquiry."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    return render_template("listing_show.html", listing=listing)

@app.route("/<permalink>/edit")
def form(permalink):
    """Allow a seller to update or unpublish a listing."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    return render_template("listing_form.html", listing=listing)

"""
Listings are placed by sellers when they want to sell things.
"""

from caravel import app, policy
from caravel.storage import helpers
from flask import render_template, request, abort, redirect, url_for
from google.appengine.api import mail

@app.route("/")
def index():
    """Display a list of listings that match the given query."""
    listings = helpers.run_query(request.args.get("q", ""))
    return render_template("index.html", listings=listings)

@app.route("/<permalink>")
def show(permalink):
    """View a particular listing and provide links to place an inquiry."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    return render_template("listing_show.html", listing=listing)

@app.route("/<permalink>/edit")
def edit(permalink):
    """Allow a seller to update or unpublish a listing."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    return render_template("listing_form.html", listing=listing)

@app.route("/<permalink>/inquiry", methods=["POST"])
def place_inquiry(permalink):
    buyer = request.form.get("email", "")

    if policy.is_authorized_buyer(buyer):
        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            buyer,
            "LISTINGNAME has received an inquiry!",
            body=render_template("email/inquiry.txt"),
            html=render_template("email/inquiry.html")
        )

    return redirect(url_for("show", permalink=permalink))

@app.route("/", methods=["POST"])
def create():
    seller = request.form.get("email", "")

    if policy.is_authorized_seller(seller):
        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            seller,
            "Welcome to Marketplace!",
            body=render_template("email/welcome.txt"),
            html=render_template("email/welcome.html")
        )

    return redirect(url_for("index"))
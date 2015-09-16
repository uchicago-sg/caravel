"""
Listings are placed by sellers when they want to sell things.
"""

import uuid, time

from flask import render_template, request, abort, redirect, url_for, session
from forms import BuyerForm, SellerForm

from google.appengine.api import mail

from caravel import app, policy
from caravel.storage import helpers, entities

@app.route("/")
def search_listings():
    """Display a list of listings that match the given query."""
    listings = helpers.run_query(request.args.get("q", ""))
    return render_template("index.html", listings=listings)

@app.route("/<permalink>", methods=['GET', 'POST'])
def show_listing(permalink):
    """View a particular listing and provide links to place an inquiry."""

    # Retrieve the listing by key.
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)

    # If the listing isn't yet published, check the ACL and update session.
    if request.args.get("key") == listing.admin_key:
        session["email"] = listing.seller
        if not listing.posting_time:
            listing.posting_time = time.time()
            listing.put()
            helpers.invalidate_listing(listing)
    elif not listing.posting_time:
        abort(404)

    buyer_form = BuyerForm()
    if buyer_form.validate_on_submit():
        return redirect(url_for("place_inquiry", permalink=permalink))

    if session.get("email") and session.get("validated"):
        buyer_form.email.data = session.get("email")
    return render_template("listing_show.html", listing=listing,
                           buyer_form=buyer_form)

@app.route("/<permalink>/edit", methods=['GET', 'POST'])
def edit_listing(permalink):
    """Allow a seller to update or unpublish a listing."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    seller_form = SellerForm
    if session.get("email") != listing.seller:
        abort(403)

    if session.get("email"):
        if session.get("validated"):
            seller_form.email.data = session.get("email")
            if seller_form.validate_on_submit():
                """ TODO (georgeteo): If already validated email address,
                then post edit directly"""
                pass
        else:
            if seller_form.validate_on_submit():
                return redirect(url_for("create", keyword="updated"))

    seller_form.title.data = listing.title
    seller_form.description = listing.body
    seller_form.price = listing.price
    # TODO (georgeteo): Do we want to reload the photos from database?
    return render_template("listing_form.html", type="Edit", listing=listing,
                           seller_form=seller_form)

@app.route("/new", methods=["GET", "POST"])
def new_listing():
    """Creates or removes this listing."""

    # Populate a form to create a listing.
    seller_form = SellerForm()

    # Actually create the listing.
    if seller_form.validate_on_submit():
        # Save a provisional version in the DB.
        seller = seller_form.seller.data
        listing = entities.Listing(
            key_name=str(uuid.uuid4()), # FIXME: add proper permalink generator.
            title=seller_form.title.data,
            price=int(seller_form.price.data * 100),
            description=seller_form.description.data,
            seller=seller,
            posting_time=0.0,
            admin_key=str(uuid.uuid4())
        )
        listing.put()
        helpers.invalidate_listing(listing)

        # Send the user an email to let them edit the listing.
        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            seller,
            "Welcome to Marketplace!",
            body=render_template("email/welcome.txt", listing=listing),
            html=render_template("email/welcome.html", listing=listing),
        )

        # Only allow the user to see the listing if they are signed in.
        if session.get("email") and session.get("validated"):
            return redirect(url_for("show_listing", permalink=listing.key_name))
        else:
            return redirect(url_for("search_listings"))

    # Have the form email default to the value from the session.
    if not seller_form.seller.data:
        seller_form.seller.data = session.get("email")

    return render_template("listing_form.html", type="New",
                           seller_form=seller_form)

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

    return redirect(url_for("show_listing", permalink=permalink))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("search_listings"))

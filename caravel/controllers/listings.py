"""
Listings are placed by sellers when they want to sell things.
"""

import uuid, time

from flask import render_template, request, abort, redirect, url_for, session
from flask import flash
import itertools

from google.appengine.api import mail

from caravel import app, policy
from caravel.storage import helpers, entities
from caravel.controllers import forms

@app.route("/")
def search_listings():
    """Display a list of listings that match the given query."""

    # Parse filtering options from query.
    query = request.args.get("q", "")
    offset = int(request.args.get("offset", "0"))
    if offset < 0:
        offset = 0

    # Compute the results matching that query.
    listings = helpers.run_query(query)
    listings = itertools.islice(listings, offset, offset + 24)

    # Render a chrome-less template for AJAH continuation.
    template = ("" if "continuation" not in request.args else "_continuation")
    return render_template("index{}.html".format(template), listings=listings)

@app.route("/<permalink>", methods=["GET", "POST"])
def show_listing(permalink):
    """View a particular listing and provide links to place an inquiry."""

    # Retrieve the listing by key.
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)

    # If the listing isn't yet published, check the URL key and update session.
    if request.args.get("key") == listing.admin_key and listing.admin_key:
        session["email"] = listing.seller
        if not listing.posting_time:
            listing.posting_time = time.time()
            listing.put()
            helpers.invalidate_listing(listing)

            flash("Your listing has been published.")
            return redirect(url_for("show_listing", permalink=permalink,
                                                    q=request.args.get("q")))

    # Otherwise, hide the listing.
    elif not listing.posting_time:
        abort(404)

    # Display a form for buyers to place an offer. 
    buyer_form = forms.BuyerForm() 

    # Handle submissions on the form.
    if buyer_form.validate_on_submit():
        buyer = buyer_form.buyer.data
        message = buyer_form.message.data

        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            listing.seller,
            "Marketplace Inquiry for {!r}".format(listing.title),
            body=render_template("email/inquiry.txt", listing=listing,
                                 buyer=buyer, message=message),
            html=render_template("email/inquiry.html", listing=listing,
                                 buyer=buyer, message=message),
            reply_to=buyer,
        )

        return redirect(url_for("show_listing", permalink=permalink))

    # Have the form email default to the value from the session.
    if not buyer_form.buyer.data:
        buyer_form.buyer.data = session.get("email")

    # Display the resulting template.
    return render_template("listing_show.html", listing=listing,
                           buyer_form=buyer_form)

@app.route("/<permalink>/claim", methods=["POST"])
def claim_listing(permalink):
    """Allow a seller to claim a listing whose email they have lost."""

    # Look up the existing listing used for this person.
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)

    # Send the user an email to let them edit the listing.
    mail.send_mail(
        "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
        listing.seller,
        "Welcome to Marketplace!",
        body=render_template("email/welcome.txt", listing=listing),
        html=render_template("email/welcome.html", listing=listing),
    )

    flash("We've emailed you a link to edit this listing.")

    return redirect(url_for("show_listing", permalink=listing.permalink))

@app.route("/<permalink>/edit", methods=["GET", "POST"])
def edit_listing(permalink):
    """Allow a seller to update or unpublish a listing."""

    # Retrieve the listing by key.
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)

    form = forms.EditListingForm()

    # Prevent non-creators from editing a listing.
    if session.get("email") != listing.seller or not session["email"]:
        abort(403)

    # Allow authors to edit listings.
    if form.validate_on_submit():
        listing.title = form.title.data
        listing.body = form.description.data
        listing.categories = form.categories.data
        listing.price = int(form.price.data * 100)
        listing.put()

        helpers.invalidate_listing(listing)

        return redirect(url_for("show_listing", permalink=listing.permalink))

    # Display an edit form.
    form.title.data = listing.title
    form.description.data = listing.body
    form.categories.data = listing.categories
    form.price.data = listing.price / 100.0

    return render_template("listing_form.html", type="Edit", form=form)

@app.route("/new", methods=["GET", "POST"])
def new_listing():
    """Creates or removes this listing."""

    # Populate a form to create a listing.
    form = forms.NewListingForm()

    # Actually create the listing.
    if form.validate_on_submit():
        # Save a provisional version in the DB.
        seller = form.seller.data
        posting_time = time.time() if session.get("email") else 0.0
        listing = entities.Listing(
            key_name=str(uuid.uuid4()), # FIXME: add proper permalink generator.
            title=form.title.data,
            price=int(form.price.data * 100),
            body=form.description.data,
            categories=form.categories.data,
            seller=seller,
            posting_time=posting_time,
            admin_key=str(uuid.uuid4())
        )
        listing.put()
        helpers.invalidate_listing(listing)

        print url_for("show_listing", permalink=listing.key().name(),
                      key=listing.admin_key, _external=True)

        # Send the user an email to let them edit the listing.
        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            seller,
            "Welcome to Marketplace!",
            body=render_template("email/welcome.txt", listing=listing),
            html=render_template("email/welcome.html", listing=listing),
        )

        # Only allow the user to see the listing if they are signed in.
        if session.get("email"):
            flash("Your listing has been published.")
            return redirect(url_for("show_listing", permalink=listing.permalink))
        else:
            flash("Your listing has been created. "
                  "Click the link in your email to publish it.")
            return redirect(url_for("search_listings"))

    # Have the form email default to the value from the session.
    if not form.seller.data:
        form.seller.data = session.get("email")

    return render_template("listing_form.html", type="New", form=form)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("search_listings"))


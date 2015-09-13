"""
Listings are placed by sellers when they want to sell things.
"""

from caravel import app, policy
from caravel.storage import helpers
from flask import render_template, request, abort, redirect, url_for, session
from google.appengine.api import mail
from forms import BuyerForm, SellerForm

@app.route("/")
def index():
    """Display a list of listings that match the given query."""
    listings = helpers.run_query(request.args.get("q", ""))
    return render_template("index.html", listings=listings)

@app.route("/<permalink>", methods=['GET', 'POST'])
def show(permalink):
    """View a particular listing and provide links to place an inquiry."""
    listing = helpers.lookup_listing(permalink)
    if not listing:
        abort(404)
    buyer_form = BuyerForm()
    if buyer_form.validate_on_submit():
        return redirect(url_for("place_inquiry", permalink=permalink))
    if session.get("email") and session.get("validated"):
        buyer_form.email.data = session.get("email")
    return render_template("listing_show.html", listing=listing,
                           buyer_form=buyer_form)

@app.route("/<permalink>/edit", methods=['GET', 'POST'])
def edit(permalink):
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

@app.route("/new", methods=['GET', 'POST'])
def new():
    """Creates a new listing"""
    seller_form = SellerForm()
    if session.get("email"):
        if session.get("validated"):
            seller_form.email.data = session.get("email")
            if seller_form.validate_on_submit():
                """ TODO (georgete): POST directly for validated emails"""
                pass
        else:
            return redirect(url_for("create", keyword="created"))
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

    return redirect(url_for("show", permalink=permalink))

@app.route("/", methods=["POST"])
def create(keyword):
    seller = request.form.get("email", "")

    if policy.is_authorized_seller(seller):
        mail.send_mail(
            "Marketplace <magicmonkeys@hosted-caravel.appspotmail.com>",
            seller,
            "Welcome to Marketplace!",
            body=render_template("email/welcome.txt"),
            html=render_template("email/welcome.html", type=keyword)
        )

    return redirect(url_for("index"))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
"""
Listings are placed by sellers when they want to sell things.
"""

from flask import render_template, request, abort, redirect, url_for, session
from flask import flash, jsonify

from werkzeug.routing import BaseConverter

from caravel import app, model, utils
from caravel.controllers import forms
from caravel.controllers import custom_fields

from google.appengine.api import users

import uuid
import datetime
import math
import itertools
import re
from google.appengine.ext import ndb

TOR_DETECTOR = utils.TorDetector()

# Allow Listings in route URLs.


class ListingConverter(BaseConverter):

    def to_python(self, value):
        listing = model.Listing.get_by_id(str(value))
        if not listing:
            abort(404)
        return listing

    def to_url(self, value):
        return value.key.string_id()

app.url_map.converters['listing'] = ListingConverter

# Allow modification of the search query in the template.


@app.template_global()
def modify_search(add=[], remove=[]):
    """Adds and removes the given words from the query, returning the new ?q."""

    query = request.args.get('q', '').split()
    query = [x.strip() for x in query if x.strip()]

    for word in remove:
        if word in query:
            query.remove(word)

    for word in add:
        if word and word not in query:
            query.append(word)

    return " ".join(query)


@app.template_global()
def login_url():
    return "/oshalogin"


@app.template_global()
def logout_url():
    return users.create_logout_url(request.url.encode("utf-8"))


@app.template_global()
def is_from_tor():
    return TOR_DETECTOR.is_tor_exit_node(request.remote_addr)


@app.context_processor
def inject_globals():
    """Adds the categories and user info into the view."""
    return {'categories_list': model.Listing.CATEGORIES_LIST,
            'categories_dict': model.Listing.CATEGORIES_DICT,
            'affiliations': model.Listing.AFFILIATIONS,
            'current_user': users.get_current_user(),
            'is_admin': users.is_current_user_admin()}

# Display the time as "1s" etc.


@app.template_filter("as_duration")
def as_duration(absolute_time):
    """
    Returns a formatted string for this duration.

    >>> import datetime
    >>> as_duration(datetime.datetime.now() + datetime.timedelta(hours=4))
    'now'
    >>> as_duration(datetime.datetime.now())
    'now'
    >>> as_duration(datetime.datetime.now() - datetime.timedelta(minutes=10))
    '11m ago'
    >>> as_duration(datetime.datetime.now() - datetime.timedelta(hours=5.5))
    '6h ago'
    """

    if not absolute_time:
        return "?"

    durations = (
        ('s', 1),
        ('m', 60),
        ('h', 60 * 60),
        ('d', 60 * 60 * 24),
        ('w', 60 * 60 * 24 * 7)
    )

    duration = (datetime.datetime.now() - absolute_time).total_seconds()
    result = "now"

    for label, length in durations:
        if length > duration:
            break
        result = "{:.0f}{} ago".format(math.ceil(duration / length), label)

    return result


@app.after_request
def show_disclaimer(response):
    session["seen_disclaimer"] = True
    return response


@app.before_request
def might_be_wrong_url():
    if (request.host == "hosted-caravel.appspot.com" and
            request.remote_addr != "0.1.0.1"):
        return redirect(request.url.replace(
            "hosted-caravel.appspot.com", "marketplace.uchicago.edu"))


@app.route("/")
def search_listings():
    """Display a list of listings that match the given query."""

    # Fix session handler if not initialized
    view = request.args.get("v", "th")

    # Parse filtering options from query.
    query = request.args.get("q", "")
    offset = int(request.args.get("offset", "0"))
    if offset < 0:
        offset = 0

    limit = 24

    # Compute the results matching that query.
    listings = list(itertools.islice(model.Listing.matching(query), offset,
                                     offset + limit))

    # Render a chrome-less template for AJAH continuation.
    template = ("" if "continuation" not in request.args else "_continuation")

    return render_template("index{}.html".format(template),
                           listings=listings, view=view, query=query)


@app.route("/<listing:listing>", methods=["GET", "POST"])
def show_listing(listing):
    """
    Retrieves a listing and displays it in the interface.
    """

    form = forms.InquiryForm()
    if form.validate_on_submit():
        if is_from_tor():
            abort(403)

        if listing.sold or listing.old:
            abort(403)

        inquiry = model.UnapprovedInquiry(listing=listing.key)
        form.populate_obj(inquiry)
        inquiry.posted_at = datetime.datetime.now()
        inquiry.put()
        if isinstance(inquiry, model.UnapprovedInquiry):
            flash("Your inquiry has been recorded and is awaiting moderation.")
        else:
            flash("Your inquiry has been sent.")
        return redirect(url_for("show_listing", listing=listing))

    return render_template("listing_show.html", listing=listing, form=form)


@app.route("/<listing:listing>/publish", methods=["POST"])
def publish_listing(listing):
    """
    Marks a listing as being published.
    """

    if is_from_tor():
        abort(403)

    requester = utils.Principal.from_request(request,
                                             email=listing.principal.email)

    if not requester.can_act_as(listing.principal):
        abort(403)

    new_listing = model.UnapprovedListing(id=listing.key.id())
    new_listing.take_values_from(listing)
    new_listing.principal = requester
    new_listing.sold = (request.form.get("sold") == "true")
    new_listing.put()

    if not isinstance(new_listing, model.Listing):
        flash("Your edit is awaiting moderation. "
              "We'll email you when it is approved.")
    return redirect(url_for("show_listing", listing=new_listing))


@app.route("/<listing:listing>/bump", methods=["POST"])
def bump_listing(listing):
    """
    Moves a listing to the top of the home page.
    """

    if is_from_tor():
        abort(403)

    requester = utils.Principal.from_request(request,
                                             email=listing.principal.email)

    if not requester.can_act_as(listing.principal) or not listing.can_bump:
        abort(403)

    new_listing = model.UnapprovedListing(id=listing.key.id())
    new_listing.take_values_from(listing)
    new_listing.principal = requester
    new_listing.posted_at = datetime.datetime.now()
    new_listing.put()

    if not isinstance(new_listing, model.Listing):
        flash("Your edit is awaiting moderation. "
              "We'll email you when it is approved.")
    return redirect(url_for("show_listing", listing=new_listing))


@app.route("/<listing:listing>/edit", methods=["GET", "POST"])
def edit_listing(listing):
    """
    Edits a listing.
    """

    if is_from_tor():
        abort(403)

    # FIXME: Clean up this logic. We intentionally don't want to expose the
    # creator of a listing.
    _principal, listing.principal = listing.principal, None
    try:
        form = forms.EditListingForm(obj=listing)
    finally:
        listing.principal = _principal

    # Ensure that we use the same principal for updates.
    form.principal.validators[-1].principal = listing.principal

    if form.validate_on_submit():
        new_listing = model.UnapprovedListing(id=listing.key.id(), version=11)
        new_listing.take_values_from(listing)
        form.populate_obj(new_listing)
        new_listing.put()

        if not isinstance(new_listing, model.Listing):
            flash("Your edit is awaiting moderation. "
                  "We'll email you when it is approved.")
        return redirect(url_for("show_listing", listing=new_listing))

    return render_template("listing_form.html", form=form)


@app.route("/_internal/cache", methods=["GET"])
def cache_info():
    return jsonify(model.utils.cache_stats())


@app.route("/new", methods=["GET", "POST"])
def new_listing():
    """
    Creates or removes a listing.
    """

    if is_from_tor():
        abort(403)

    form = forms.NewListingForm()

    if form.validate_on_submit():
        listing = model.UnapprovedListing(id=str(uuid.uuid4()), version=11)
        form.populate_obj(listing)
        listing.posted_at = datetime.datetime.now()
        listing.put()

        if isinstance(listing, model.Listing):
            flash("Your listing has been created.")
            return redirect(url_for("show_listing", listing=listing))
        else:
            flash("Your listing is awaiting moderation. "
                  "We'll email you when it's up.")
            return redirect(url_for("search_listings"))

    return render_template("listing_form.html", form=form)


@app.route("/oshalogin", methods=["GET", "POST"])
@app.route("/nooshalogin", methods=["GET", "POST"])
def login_page():
    affiliation = request.form.get("affiliation", "")
    affiliation = request.args.get("affiliation", affiliation)
    email = request.args.get("email", request.form.get("email", ""))

    if affiliation not in dict(model.Listing.AFFILIATIONS):
        affiliation = ""

    if not re.match(r'^\S+@\S+$', email) or users.get_current_user():
        email = ""

    session["affiliation"] = affiliation
    session["email"] = email

    return redirect("/")

from caravel.storage import dos, email, config

import itertools

from wtforms.validators import ValidationError
from flask import session, redirect, request, render_template

PLEASE_TRY_AGAIN_LATER = "Please slow down and try again later."
INVALID_EMAIL = "You can only submit listings from a UChicago email address."

WHITELISTED_ACCOUNTS = [
    "eahme1@ikumon.com"
]

BLACKLISTED_ACCOUNTS = [
    "globarry24@gmail.com",
    "valenciae49@yahoo.com"
]

def signed_in(inquiry):
    """
    Determines if we're able to access the given listing.
    """
    return inquiry.seller == session.get("email") and session["email"]

def is_too_frequent(principals, rates):
    """
    Use all of the given buckets from acting faster than the given rates.
    """
    for ident, (limit, time_range) in itertools.product(principals, rates):
        if dos.rate_limit(ident, limit, time_range):
            return True
    return False

def is_from_tor():
    """
    Prevent clients from using Tor IP addresses to interact with Marketplace.
    """
    return request.remote_addr in config.get_tor_addresses()

def is_campus_address(email):
    """
    Ensures that the given email is an on-campus address.
    """

    if is_banned(email):
        return False

    try:
        user, domain = email.split("@")
        if domain in ("uchicago.edu", "uchospitals.edu", "chicagobooth.edu"):
            return True
    except ValueError:
        pass

    return email in WHITELISTED_ACCOUNTS

def is_banned(email):
    """
    Ensures that the given email is allowed to post inquiries on Marketplace.
    """

    return email in BLACKLISTED_ACCOUNTS

def block(should_block, error=None):
    """
    Blocks a user from performing the given action.
    """

    if should_block:
        raise ValidationError, (error or PLEASE_TRY_AGAIN_LATER)

def place_inquiry(listing, buyer, message):
    """
    Control the creation of inquiries for each listing.
    """

    # Block addresses commonly used for posting spam.
    block(is_from_tor())

    # Block users that are banned from Marketplace.
    block(is_banned(buyer))

    # Make sure the user only submits a fixed count at given time.
    principal = [buyer, listing.permalink, request.remote_addr]
    block(is_too_frequent(principal, [(4, 60), (100, 24 * 3600)]))

    # Send a message to the user with a link to edit the listing.
    is_signed_in = signed_in(listing)
    email.send_mail(
        to=listing.seller,
        reply_to=buyer,
        subject=u"Re: Marketplace Listing \"{}\"".format(listing.title),
        html=render_template("email/inquiry.html", **locals()),
        text=render_template("email/inquiry.txt", **locals()),
    )

def claim_listing(listing):
    """
    Control the creation of new listings.
    """

    # Block inquiries from non-UChicago email addresses.
    block(not is_campus_address(listing.seller),
        error="Please only post listings with a UChicago email address.")

    # Block addresses commonly used for posting spam.
    block(is_from_tor())

    # Make sure the user only submits a fixed count at given time.
    block(is_too_frequent([listing.permalink], [(1, 24 * 3600)]))
    block(is_too_frequent([request.remote_addr], [(4, 60)]))

    # Send a message to the user with a link to edit the listing.
    is_signed_in = signed_in(listing)
    email.send_mail(
        to=listing.seller,
        subject=u"Marketplace Listing \"{}\"".format(listing.title),
        html=render_template("email/welcome.html", **locals()),
        text=render_template("email/welcome.txt", **locals()),
    )

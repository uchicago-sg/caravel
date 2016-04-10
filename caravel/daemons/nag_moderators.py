"""
This daemon automatically removes photos that are too old.
"""

from caravel import app, model, utils
from caravel.utils import emails
from flask import render_template
from google.appengine.api import users


@app.route('/_internal/nag_moderators')
def nag_moderators():
    listings = list(model.UnapprovedListing().query())
    inquiries = list(model.UnapprovedInquiry().query())
    pending = listings + inquiries

    if pending == []:
        return "none"

    emails._send_raw_mail(
        to="marketplace@lists.uchicago.edu",
        subject="{} Inquiries, {} Listings Pending".format(
            len(inquiries), len(listings)),
        text=render_template("email/nag_moderators.txt",
                             listings=listings, inquiries=inquiries),
        html=None
    )

    return "ok"

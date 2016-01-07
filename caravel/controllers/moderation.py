import datetime

from caravel import model, app
from caravel.model import moderation
from flask import render_template, url_for, request
import user_agents

from google.appengine.ext import ndb
from google.appengine.api import users


@app.template_global()
def user_agent(user_agent):
    return str(user_agents.parse(user_agent))


@app.route("/moderation", methods=["GET", "POST"])
def moderation_view():
    """
    Approves or denies a listing or inquiry.
    """

    # Ensure that the current user is an admin.
    assert users.get_current_user() and users.is_current_user_admin()

    # Approve something, if we were asked to.
    if request.form.get("approve"):
        key = ndb.Key(urlsafe=request.form.get("approve"))
        if key.kind() not in ["UnapprovedListing", "UnapprovedInquiry"]:
            raise ValueError

        entity = key.get()
        entity.approve("Approved by {!r} on {!r}".format(
            users.get_current_user().email(),
            str(datetime.datetime.now())
        ))
        entity.put()
        return ""

    elif request.form.get("deny"):
        key = ndb.Key(urlsafe=request.form.get("deny"))
        if key.kind() not in ["UnapprovedListing", "UnapprovedInquiry"]:
            raise ValueError

        entity = key.get()
        entity.deny("Denied by {!r} on {!r}".format(
            users.get_current_user().email(),
            str(datetime.datetime.now())
        ))
        entity.put()
        return ""

    inquiries = model.UnapprovedInquiry().query().fetch(100)
    listings = model.UnapprovedListing().query().fetch(100)

    return render_template("moderation/view.html",
                           inquiries=inquiries,
                           listings=listings)

import datetime

from caravel import model, app
from caravel.model import moderation
from flask import render_template, url_for, request
import user_agents
import itertools
import re

from google.appengine.ext import ndb
from google.appengine.api import users


class ModerationConfig(ndb.Model):
    """
    Defines the static configuration of the automoderator.
    """

    @classmethod
    def get(klass):
        return klass.get_or_insert("singleton")

    enabled = ndb.BooleanProperty(default=False)
    blacklist = ndb.StringProperty(repeated=True)  # defaults to []
    min_delay = ndb.IntegerProperty(default=0)


@app.template_global()
def user_agent(user_agent):
    return str(user_agents.parse(user_agent))


def email_order(entity):
    user, domain = entity.principal.email.split("@")
    return (domain, user)


@app.route("/moderation", methods=["GET", "POST"])
def moderation_view():
    """
    Approves or denies a listing or inquiry.
    """

    # Ensure that the current user is an admin.
    assert users.get_current_user() and users.is_current_user_admin()

    config = ModerationConfig.get()

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

        key.delete()
        return ""

    if request.form.get("automod"):
        if config.enabled:
            config.blacklist = [x.strip() for x in
                                request.form.get("blacklist", "").split("\n")
                                if x.strip()]
            config.min_delay = int(request.form.get("min_delay", "0"))
        config.enabled = (request.form.get("automod") == "true")
        config.put()

    inquiries = model.UnapprovedInquiry().query().fetch(100)
    listings = model.UnapprovedListing().query().fetch(100)

    inquiries.sort(key=email_order)
    listings.sort(key=email_order)

    return render_template("moderation/view.html",
                           inquiries=inquiries,
                           listings=listings,
                           config=config)


@app.route("/_internal/automod")
def automod():
    if not users.is_current_user_admin():
        return "???"

    pending = itertools.chain(
        model.UnapprovedListing().query(),
        model.UnapprovedInquiry().query(),
    )

    config = ModerationConfig.get()
    if not config.enabled:
        return ""

    for to_moderate in pending:
        if to_moderate.age < datetime.timedelta(minutes=config.min_delay):
            continue

        values = dict(to_moderate.to_dict())
        values["principal"] = values["principal"].email
        allowed = True

        for field in values.values():
            for item in config.blacklist:
                if re.match(item, unicode(field)):
                    allowed = False

        if allowed:
            to_moderate.approve(
                "Approved by Automod(blacklist={!r}) on {!r}".format(
                    config.blacklist,
                    str(datetime.datetime.now())))
            to_moderate.put()

    return "ok"

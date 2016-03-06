from google.appengine.ext import ndb

from caravel import utils
from caravel.model import listing

from caravel.model.moderation import ModeratedMixin
from caravel.model.temporal import TimeOrderMixin
from caravel.model.principal import PrincipalMixin
from caravel.model.side_effects import SideEffectsMixin
from caravel.model.rate_limits import RateLimitMixin
from caravel.model.replication import ReplicationMixin


from flask import render_template


class _Inquiry(TimeOrderMixin, PrincipalMixin, ModeratedMixin,
               ReplicationMixin, ndb.Model):

    REPLICATION_URL = "https://go-marketplace.appspot.com/inquiries"

    message = ndb.StringProperty()
    listing = ndb.KeyProperty(kind=listing.Listing)

    def encode_for_replication(self):
        """Flattens this Listing into a JSON dict."""

        data = self.to_dict()
        data["listing"] = self.listing.id()
        data["sender"] = {
            "email": self.principal.email,
            "validated": (self.principal.auth_method == "GOOGLE_APPS")
        }
        data["moderated"] = (bool(self.principal.validated_by) or
                             (self.principal.auth_method == "GOOGLE_APPS"))
        del data["principal"]
        del data["posted_at"]
        if "run_trigger" in data:
            del data["run_trigger"]

        return data


class Inquiry(SideEffectsMixin, _Inquiry):

    def side_effects(self):
        """
        Sends an email to the owner of this listing letting them know of the
        inquiry.
        """

        listing = self.listing.get()
        utils.send_mail(
            to=listing.principal,
            reply_to=self.principal,
            subject=u"Re: Marketplace Listing \"{}\"".format(listing.title),
            html=render_template("email/inquiry.html",
                                 listing=listing, inquiry=self),
            text=render_template("email/inquiry.txt",
                                 listing=listing, inquiry=self)
        )


class UnapprovedInquiry(_Inquiry):
    MAX_DAILY_LIMIT = 5
    TYPE_ONCE_APPROVED = Inquiry

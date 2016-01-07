from google.appengine.ext import ndb

from caravel import utils
from caravel.model import listing

from caravel.model.moderation import ModeratedMixin
from caravel.model.temporal import TimeOrderMixin
from caravel.model.principal import PrincipalMixin
from caravel.model.side_effects import SideEffectsMixin
from caravel.model.rate_limits import RateLimitMixin

from flask import render_template


class _Inquiry(TimeOrderMixin, PrincipalMixin, ModeratedMixin,
               ndb.Model):
    message = ndb.StringProperty()
    listing = ndb.KeyProperty(kind=listing.Listing)


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

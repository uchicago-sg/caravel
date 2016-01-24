from google.appengine.ext import ndb, db
from caravel.utils import Principal, Device
from caravel.model.moderation import ModeratedMixin
from caravel.model.temporal import TimeOrderMixin
from caravel.model.categories import CategoriesMixin
from caravel.model.attachments import PhotosMixin, Photo
from caravel.model.migration import SchemaMixin
from caravel.model.priced import PriceMixin
from caravel.model.principal import PrincipalMixin
from caravel.model.side_effects import SideEffectsMixin
from caravel.model.full_text import FullTextMixin
from caravel.model.rate_limits import RateLimitMixin
from caravel.model.sellable import SellableMixin

from caravel import utils

import datetime
import re
from flask import render_template


class _Listing(CategoriesMixin, PhotosMixin, PrincipalMixin, TimeOrderMixin,
               SchemaMixin, PriceMixin, RateLimitMixin, ModeratedMixin,
               SellableMixin, FullTextMixin, ndb.Model):

    SCHEMA_VERSION = 12
    MARK_AS_OLD_AFTER = datetime.timedelta(days=30)

    title = ndb.StringProperty()
    body = ndb.TextProperty()


class Listing(SideEffectsMixin, _Listing):

    def side_effects(self):
        """
        Sends an email to the creator of this listing.
        """

        utils.send_mail(
            to=self.principal,
            subject=u"Marketplace Listing \"{}\"".format(self.title),
            html=render_template("email/listing_verified.html", listing=self),
            text=render_template("email/listing_verified.txt", listing=self)
        )

    def _keywords(self):
        """Generates keywords for this listing."""

        if self.sold or self.old:
            return []

        keywords = (
            self._tokenize("title", self.title) +
            self._tokenize("body", self.body) +
            self._tokenize("category", " ".join(self.categories)) +
            self._tokenize("seller", self.principal.email)
        )
        if self.price == 0:
            keywords.append("price:free")
        return keywords


class UnapprovedListing(_Listing):
    MAX_DAILY_LIMIT = 4
    TYPE_ONCE_APPROVED = Listing


@Listing.migration(to_version=11)
def to_ndb_schema(listing):
    if hasattr(listing, "details"):
        listing.title, listing.body = listing.description, listing.details

    if not listing.categories:
        listing.categories = ["miscellaneous"]

    listing.principal = Principal(
        email=listing.seller,
        device=Device("autogen", "(unknown)", "0.0.0.0"),
        auth_method=Principal.LEGACY
    )

    if hasattr(listing, "posting_time"):
        listing.posted_at = (
            datetime.datetime.fromtimestamp(listing.posting_time))
    else:
        listing.posted_at = datetime.datetime(month=9, day=15, year=2015)

    listing.categories = [re.sub(r'^category:', '', x) for x in
                          listing.categories]

    listing.photos = [
        Photo(re.sub(r'-large$', '', p.path)) for p in listing.photos]
    listing.run_trigger = True

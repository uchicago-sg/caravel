from caravel.tests import helper
from caravel import model

import datetime
from google.appengine.ext import db


class Listing(db.Expando):

    """An old-style Listing."""

    version = db.IntegerProperty()

    seller = db.StringProperty()  # an email address
    title = db.StringProperty(default="")
    body = db.TextProperty(default="")
    price = db.IntegerProperty(default=0)  # in cents of a U.S. dollar
    posting_time = db.FloatProperty(default=0.0)  # 0 iff not yet published
    categories = db.StringListProperty()  # stored as keys of CATEGORIES
    admin_key = db.StringProperty(default="")  # how to administer this listing
    buyers = db.StringListProperty()  # how many people are interested

    photos = db.StringListProperty(indexed=False)
    thumbnails = db.StringListProperty(indexed=False)


class TestListings(helper.CaravelTestCase):

    def test_migrate_from_old(self):

        # Post an old version Listing.
        Listing(
            key_name="my-listing-name",
            seller="jarcher@uchicago.edu",
            title=u"Legacy \xe2\x98\x86",
            body=u"Body of Legacy \xe2\x98\x86",
            price=4224,
            posting_time=1450075937.907662,
            categories=["category:furniture", "category:bikes"],
            admin_key="4242",
            buyers=["a@domain.com", "b@domain.com"],
            photos=["aa-bb", "cc-dd"],
            version=10,
        ).put()

        # Verify that gets now receive the correct version.
        listing = model.Listing.get_by_id("my-listing-name")
        self.assertEquals(listing.key.id(), "my-listing-name")
        self.assertEquals(repr(listing.principal),
                      "Principal("
                      "email='jarcher@uchicago.edu', "
                      "device=Device(nonce='autogen', user_agent='(unknown)',"
                      " ip_address='0.0.0.0'), "
                      "auth_method='LEGACY')")

        self.assertEquals(listing.title, u"Legacy \xe2\x98\x86")
        self.assertEquals(listing.body, u"Body of Legacy \xe2\x98\x86")
        self.assertEquals(listing.price, 42.24)
        self.assertEquals(int((
                            listing.posted_at -
                            datetime.datetime.fromtimestamp(1450075938)
                          ).total_seconds()), 0)
        self.assertEquals(listing.categories, ["furniture", "bikes"])
        self.assertEquals(listing.photos[0].path, "aa-bb")
        self.assertEquals(listing.photos[1].path, "cc-dd")
        self.assertEquals(listing.version, 11)

        # Trigger an update cronjob.
        self.get("/_internal/migrate_schema")

        # Verify that we have now changed on disk.
        listing = Listing.get_by_key_name("my-listing-name")
        self.assertEquals(listing.version, 11)

        # Verify that no emails were sent.
        self.assertEquals(self.emails, [])

    def test_migrate_from_super_old(self):

        # Post a super old listing.
        Listing(
            key_name="second-listing-name",
            seller="jarcher@uchicago.edu",
            description=u"Legacy \xe2\x98\x86",
            details=u"Body of Legacy \xe2\x98\x86",
            price=4224,
            posting_time=1450075937.907662,
            admin_key="4242",
            buyers=["a@domain.com", "b@domain.com"],
            photos=["aa-bb", "cc-dd"]
        ).put()

        # Verify that making a query gets the correct listing.
        listing = model.Listing.query(model.Listing.price == 42.24).get()
        self.assertEquals(listing.title, u"Legacy \xe2\x98\x86")
        self.assertEquals(listing.body, u"Body of Legacy \xe2\x98\x86")
        self.assertEquals(listing.categories, ["miscellaneous"])

        # Verify that gets now receive the correct version.
        listing = model.Listing.get_by_id("second-listing-name")
        self.assertEquals(listing.title, u"Legacy \xe2\x98\x86")
        self.assertEquals(listing.body, u"Body of Legacy \xe2\x98\x86")
        self.assertEquals(listing.categories, ["miscellaneous"])

        # Verify that no emails were sent.
        self.assertEquals(self.emails, [])

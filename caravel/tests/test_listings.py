from caravel.storage import config
from caravel.tests import helper
from caravel import model
from caravel.model import utils

import unittest
import StringIO
import time
import re
import datetime
import json


class TestListings(helper.CaravelTestCase):

    def test_indexing(self):
        # Test normal indexing.
        self.assertFalse(self.listing_a.old)
        self.assertLongString("\n".join(sorted(self.listing_a.keywords)))

        # Test that old listings are de-indexed.
        self.listing_a.posted_at = datetime.datetime(2003, 2, 3)

        self.assertTrue(self.listing_a.old)
        self.assertEquals(self.listing_a.keywords, [])

        # Test that sold listings are de-indexed.
        self.listing_b.sold = True
        self.assertEquals(self.listing_a.keywords, [])

    def test_search(self):
        # View all listings, in order.
        self.assertLongString(self.get("/").data)

        # View listings in list view
        self.assertLongString(self.get("/?v=ls").data)

        # Listings at an offset.
        self.assertLongString(self.get("/?offset=1").data)

        # Just a subset of listings.
        self.assertLongString(self.get("/?q=body+%E2%98%86a").data)

        # Make sure links work.
        self.assertIn("/listing_a", self.get("/?q=body+%E2%98%86a").data)

        # Make sure the right photos show up.
        self.assertEqual(self.extract_photos(self.get("/").data), [
            "/static/images/logo.jpg",
            "/_ah/gcs/test.appspot.com/listing-a-small",
            "/_ah/gcs/test.appspot.com/listing-b-small"
        ])

    def test_post_inquiry(self):
        # Submit an inquiry.
        self.post("/listing_b", data={
            "principal": "buyer@foo.com",
            "affiliation": "alumni",
            "message": u"message\u2606 goes here",
            "csrf_token": self.csrf_token("/listing_b"),
        })

        # Even so, ensure that it seems as though it got through.
        self.assertLongString(self.get("/listing_b").data)

        # Ensure that no emails have been sent.
        self.assertEqual(self.emails, [])

        # Notify the moderators that something has happened.
        with self.google_apps_user("admin@uchicago.edu"):
            self.get("/_internal/nag_moderators")

        # Ensure that the moderators received the right email.
        self.assertEqual(
            self.emails[0].to[0],
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
                         "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
                         u"1 Inquiries, 0 Listings Pending")

        self.assertLongString(self.emails[0].text)
        self.emails.pop(0)

        # Approve the first inquiry.
        with self.google_apps_user("admin@uchicago.edu"):
            print self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedInquiry.query().get().key.urlsafe(),
            }).data

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "seller-b@uchicago.edu")
        self.assertEqual(self.emails[0].reply_to, "buyer@foo.com")
        self.assertEqual(self.emails[0].from_email,
                         "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
                         u"Re: Marketplace Listing \"Listing \u2606B\"")

        # Verify that the right message text was sent.
        self.assertLongString(self.emails[0].text)

        # Verify that the right messge HTML was sent.
        self.assertLongString(self.emails[0].html)

    def test_post_inquiry_with_cnetid(self):
        # Submit an inquiry.
        with self.google_apps_user("visitor@uchicago.edu"):
            self.post("/listing_b", data={
                "principal": "buyer@foo.com",
                "message": u"message\u2606 goes here",
                "affiliation": "osha_current_student",
                "csrf_token": self.csrf_token("/listing_b"),
            })

            # Ensure that we display a helpful message.
            self.assertLongString(self.get("/listing_b").data)

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "seller-b@uchicago.edu")
        self.assertEqual(self.emails[0].reply_to, "visitor@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
                         "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
                         u"Re: Marketplace Listing \"Listing \u2606B\"")

        # Verify that the right message text was sent.
        self.assertLongString(self.emails[0].text)

        # Verify that the right messge HTML was sent.
        self.assertLongString(self.emails[0].html)

    def test_new_listing(self):
        # Try creating a new listing as an unauthenticated user.
        self.post("/new", data={
            "csrf_token": self.csrf_token("/new"),
            "title": u"Title of \u2606D",
            "body": u"Body of \u2606D",
            "price": "3.441",
            "principal": "seller-d@uchicago.edu",
            "affiliation": "alumni",
            "categories": "apartments",
            "uploaded_photos-2-image":
                ("caravel/tests/test-pattern.gif", "t.jpg")
        })

        # Ensure that we get a message indicating that it does not exist.
        self.assertLongString(self.get("/").data)

        # Ensure that the listing does not exist yet.
        self.assertLongString(self.get("/ZZ-ZZ-ZZ").data)

        # Ensure that no emails have been sent.
        self.assertEqual(self.emails, [])

        # Approve the first listing.
        with self.google_apps_user("admin@uchicago.edu"):
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedListing.query().get().key.urlsafe(),
            })

        # Listing is now published.
        self.assertLongString(self.get("/ZZ-ZZ-ZZ").data)

        # Make sure the picture shows up.
        photos = self.extract_photos(self.get("/ZZ-ZZ-ZZ").data)
        now = photos[1].split("/")[4].split("-")[0]
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-large'.format(now)
        ])

        # Listing shows up in searches.
        self.assertLongString(self.get("/").data)

        # Verify that this listing has a photo.
        photos = self.extract_photos(self.get("/").data)
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-small'.format(now),
            '/_ah/gcs/test.appspot.com/listing-a-small',
            '/_ah/gcs/test.appspot.com/listing-b-small',
        ])

    def test_edit_listing_with_cnetid(self):
        pass

    def test_new_listing_with_cnetid(self):
        # Try creating a new listing as an authenticated user.
        with self.google_apps_user("visitor@uchicago.edu"):
            self.post("/new", data={
                "csrf_token": self.csrf_token("/new"),
                "title": u"Title of \u2606D",
                "body": u"Body of \u2606D",
                "price": "3.441",
                "categories": "apartments",
                "affiliation": "osha_current_student",
                "uploaded_photos-2-image":
                    ("caravel/tests/test-pattern.gif", "t.jpg")
            })

            # Listing is now published.
            self.assertLongString(self.get("/ZZ-ZZ-ZZ").data)

        # Make sure the picture shows up.
        photos = self.extract_photos(self.get("/ZZ-ZZ-ZZ").data)
        now = photos[1].split("/")[4].split("-")[0]
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-large'.format(now)
        ])

        # Listing shows up in searches.
        self.assertLongString(self.get("/").data)

        # Verify that this listing has a photo.
        photos = self.extract_photos(self.get("/").data)
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-small'.format(now),
            '/_ah/gcs/test.appspot.com/listing-a-small',
            '/_ah/gcs/test.appspot.com/listing-b-small',
        ])

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "visitor@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
                         "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
                         u"Marketplace Listing \"Title of \u2606D\"")

        # Verify that the right message text was sent.
        self.assertLongString(self.emails[0].text)

        # Verify that the right messge HTML was sent.
        self.assertLongString(self.emails[0].html)

    def test_edit_listing(self):
        # Try editing someone else's listing.
        self.assertLongString(self.post("/listing_a/edit", data=dict(
            csrf_token=self.csrf_token("/listing_a/edit"),
            title=u"Title\u2606A",
            body=u"Body\u2606A",
            price="2.34",
            principal="seller-a@uchicago.edu",
            categories="cars",
        )).data)

        # Try editing our own listing.
        with self.google_apps_user("seller-a@uchicago.edu"):
            self.post("/listing_a/edit", data=dict(
                csrf_token=self.csrf_token("/listing_a/edit"),
                title=u"Title\u2606A",
                body=u"Body\u2606A",
                price="2.34",
                principal="",
                categories="cars",
            ))

            self.assertLongString(self.get("/listing_a").data)

    def test_publish_listing(self):
        self.post("/listing_b/publish", data=dict(
            csrf_token=self.csrf_token("/listing_b"),
            sold="true"
        ))

        # Listing is not yet sold.
        self.assertLongString(self.get("/listing_b").data)

        # Approve the edit.
        with self.google_apps_user("admin@uchicago.edu"):
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedListing.query().get().key.urlsafe(),
            }).data

        # The listing is sold now!
        self.assertLongString(self.get("/listing_b").data)

        # Listing is no longer visible in searches.
        self.assertLongString(self.get("/").data)
        self.assertLongString(self.get("/?q=listing").data)

        # Try unmarking a listing as sold.
        self.post("/listing_b/publish", data=dict(
            csrf_token=self.csrf_token("/listing_b/edit"),
            sold="false"
        ))

        # Listing is still sold.
        self.assertLongString(self.get("/listing_b").data)

        # Approve the edit.
        with self.google_apps_user("admin@uchicago.edu"):
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedListing.query().get().key.urlsafe(),
            }).data

        # Listing is no longer sold.
        self.assertLongString(self.get("/listing_b").data)

        # Listing is visible again in searches.
        self.assertLongString(self.get("/").data)

    def test_publish_listing_with_cnetid(self):
        with self.google_apps_user("seller-b@uchicago.edu"):
            # Try marking a listing as sold.
            self.post("/listing_a/publish", data=dict(
                csrf_token=self.csrf_token("/listing_a"),
                sold="true"
            ))

            # Listing is now sold.
            self.assertLongString(self.get("/listing_a").data)

            # Listing is no longer visible in searches.
            self.assertLongString(self.get("/").data)
            self.assertLongString(self.get("/?q=listing").data)

            # Try unmarking a listing as sold.
            self.post("/listing_a/publish", data=dict(
                csrf_token=self.csrf_token("/listing_a/edit"),
                sold="false"
            ))

            # Listing is no longer sold.
            self.assertLongString(self.get("/listing_a").data)

            # Listing is visible again in searches.
            self.assertLongString(self.get("/").data)

    def test_old_listing(self):
        self.listing_a.posted_at -= datetime.timedelta(days=60)
        self.listing_a.put()

        self.assertLongString(self.get("/listing_a").data)

    def test_bump_listing(self):
        # Test the can_bump property.
        self.assertFalse(self.listing_a.can_bump)
        self.listing_a.posted_at -= datetime.timedelta(days=10)
        self.listing_a.put()
        self.assertTrue(self.listing_a.can_bump)

        # Try to bump a listing.
        self.assertLongString(self.get("/listing_a").data)
        with self.google_apps_user("seller-a@uchicago.edu"):
            self.post("/listing_a/bump", data={
                "csrf_token": self.csrf_token("/listing_a/edit"),
            })

        self.listing_a = self.listing_a.key.get()
        self.assertFalse(self.listing_a.can_bump)
        self.assertTrue(self.listing_a.age <= datetime.timedelta(seconds=60))

    def test_cache(self):
        # Warm the cache.
        self.get("/")
        self.get("/listing_a")
        self.get("/favicon.ico")
        self.get("/apartments.atom")

        # Make sure future reads do not hit the database.
        before = utils.cache_stats()
        for i in xrange(20):
            self.get("/")
            self.get("/listing_a")
            self.get("/favicon.ico")
            self.get("/apartments.atom")
        after = utils.cache_stats()

        self.assertEquals(before["invalidations"], after["invalidations"])
        self.assertEquals(before["misses"], after["misses"])
        self.assertGreaterEqual(after["hits"] - before["hits"], 20)

        self.assertEqual(
            json.loads(self.get("/_internal/cache").data), after
        )

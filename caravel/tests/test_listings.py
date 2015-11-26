from caravel.storage import entities, config
from caravel.tests import helper

import StringIO
import time
import re

class TestListings(helper.CaravelTestCase):
    def test_search(self):
        # View all listings, in order.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Listing \xe2\x98\x86A 5h ago Cars $3.10 Listing "
            "\xe2\x98\x86B 2d ago Apartments $71.10")

        # Listings at an offset.
        self.assertEqual(self.clean(self.get("/?offset=1").data),
            "New Listing Listing \xe2\x98\x86B 2d ago Apartments $71.10")

        # Just a subset of listings.
        self.assertEqual(self.clean(self.get("/?q=body+%E2%98%86a").data),
            "New Listing Listing \xe2\x98\x86A 5h ago Cars $3.10")

        # Make sure links work.
        self.assertIn("/listing_a", self.get("/?q=body+%E2%98%86a").data)

        # Make sure the right photos show up.
        self.assertEqual(self.extract_photos(self.get("/").data), [
            "/static/images/logo.jpg",
            "/_ah/gcs/test.appspot.com/listing-a-small",
            "/_ah/gcs/test.appspot.com/listing-b-small"
        ])

    def test_inquiry(self):
        # Submit an inquiry.
        self.post("/listing_b", data=dict(
            buyer="buyer@foo.com",
            message=u"message\u2606 goes here",
            csrf_token=self.csrf_token("/listing_b"),
        ))

        # Verify that the UI is updated.
        self.assertEqual(self.clean(self.get("/listing_b").data),
            "New Listing Your inquiry has been sent. Listing \xe2\x98\x86B "
            "Apartments $71.10 Body of \xe2\x98\x86B Contact Seller This "
            "listing has 1 inqury. Email UChicago Email Preferred Message")

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "seller-b@uchicago.edu")
        self.assertEqual(self.emails[0].reply_to, "buyer@foo.com")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            u"Re: Marketplace Listing \"Listing \u2606B\"")

        # Verify that the right message text was sent.
        self.assertEqual(self.emails[0].text,
            u"Hello again!\n\n"
            u"We've received a new inquiry for Listing \u2606B:\n\n"
            u"  Buyer: buyer@foo.com (IP: None)\n"
            u"  \n"
            u"  message\u2606 goes here\n\n"
            u"Simply reply to this email if you'd like to get in contact.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team"
        )

        # Verify that the right messge HTML was sent.
        self.assertEqual(self.clean(self.emails[0].html),
            u"My Test Email Marketplace Hello again! We've received a new "
            u"inquiry for Listing \u2606B: Buyer: buyer@foo.com (IP: None) "
            u"message\u2606 goes here Simply reply to this email if you'd "
            u"like to get in contact. Cheers, The Marketplace Team")

        # Verify that we were sent a chat message.
        self.assertEqual(self.chats, [{
            "icon_url": u"/_ah/gcs/test.appspot.com/listing-b-small",
            "text": u"Inquiry by buyer@foo.com",
            "username": u"Listing \u2606B"
        }])

    def test_new_listing(self):
        # Try creating a new listing as an authenticated user.
        self.post("/new", data={
            "csrf_token": self.csrf_token("/new"),
            "title": u"Listing \u2606D",
            "description": u"Listing \u2606D",
            "seller": "seller-d@uchicago.edu",
            "categories": "category:books",
            "photos-0-image": ("caravel/tests/test-pattern.gif", "t.jpg")
        })

        # Verify that the listing does not exist yet.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Your listing has been created. Click the link in "
            "your email to publish it. Listing \xe2\x98\x86A 5h ago Cars "
            "$3.10 Listing \xe2\x98\x86B 2d ago Apartments $71.10")

        # Verify that we were sent a chat message.
        self.assertEqual(self.chats, [{
            "icon_url": None,
            "text": (u"Posted by seller-d@uchicago.edu "
                      u"(<http://localhost/ZZ-ZZ-ZZ?key=ZZ-ZZ-ZZ|approve>)"),
            "username": u"Listing \u2606D"
        }])

        # Ensure that we were sent a link to edit a listing.
        self.assertEqual(self.emails[0].to[0], "seller-d@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            u"Marketplace Listing \"Listing \u2606D\"")

        self.assertEqual(self.emails[0].text,
            u"Hello there, and welcome to Marketplace!\n\n"
            u"Your listing has been created. Please click the link below "
            u"to edit it.\n\n"
            u"  http://localhost/ZZ-ZZ-ZZ?key=ZZ-ZZ-ZZ\n\n"
            u"Important: you'll need to click this link at least once for "
            u"your listing to\nbe viewable by others -- this is to protect "
            u"against spam.\n\nIf you didn't create this listing, you can "
            u"safely ignore this email. It was\ncreated by None; please "
            u"contact us if anything seems\nstrange.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team")

        # Verify that the email looks fine.
        self.assertEqual(self.clean(self.emails[0].html),
            u"Welcome to Marketplace Marketplace Hello there, and welcome to "
            u"Marketplace! Your listing has been created. Please click the "
            u"button below to edit it. Edit \"Listing \u2606D\" Important: "
            u"you'll need to click this link at least once for your "
            u"listing to be viewable by others &mdash; this is to protect "
            u"against spam. If you didn't create this listing, you can "
            u"safely ignore this email. It was created by None; please "
            u"contact us if anything seems strange. Cheers, The "
            u"Marketplace Team")

        # Click the link in the message.
        page = self.get("/ZZ-ZZ-ZZ?key=ZZ-ZZ-ZZ")

        # Listing is now published.
        self.assertEqual(self.clean(self.get("/ZZ-ZZ-ZZ").data),
            "New Listing Logged in as seller-d@uchicago.edu My Listings "
            "Logout Your listing has been published. Listing "
            "\xe2\x98\x86D Books $0.00 Listing \xe2\x98\x86D Manage "
            "Listing Edit")

        # Listing has the correct photo.
        photos = self.extract_photos(self.get("/ZZ-ZZ-ZZ").data)
        now = int(photos[1].split("/")[4].split("-")[0])
        self.assertEqual(photos,
            ["/static/images/logo.jpg",
             "/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-large".format(now)])

        # Listing shows up in searches.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Logged in as seller-d@uchicago.edu My Listings "
            "Logout Listing \xe2\x98\x86D now ago Books $0.00 Listing "
            "\xe2\x98\x86A 5h ago Cars $3.10 Listing \xe2\x98\x86B 2d "
            "ago Apartments $71.10")

        # Listing has correct photo in listings.
        self.assertEqual(self.extract_photos(self.get("/").data),
            ["/static/images/logo.jpg",
             "/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-small".format(now),
             "/_ah/gcs/test.appspot.com/listing-a-small",
             "/_ah/gcs/test.appspot.com/listing-b-small"])

    def test_claim_listing(self):
        # View a listing and click "Claim"
        self.post("/listing_a/claim", data=dict(
            csrf_token=self.csrf_token("/listing_a")
        ))

        # Ensure that the flash shows up.
        self.assertEqual(self.clean(self.get("/listing_a").data),
            "New Listing We&#39;ve emailed you a link to edit this listing. "
            "Listing \xe2\x98\x86A Cars $3.10 Body of \xe2\x98\x86A Contact "
            "Seller Email UChicago Email Preferred Message")

        # Ensure that the message is as we expect.
        self.assertEqual(self.emails[0].to[0], "seller-a@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            u"Marketplace Listing \"Listing \u2606A\"")

        # Verify the textual contents of the message.
        self.assertEqual(self.emails[0].text,
            u"Hello there, and welcome to Marketplace!\n\n"
            u"Your listing has been created. Please click the link below "
            u"to edit it.\n\n"
            u"  http://localhost/listing_a?key=a_key\n\n"
            u"Important: you'll need to click this link at least once for "
            u"your listing to\nbe viewable by others -- this is to protect "
            u"against spam.\n\nIf you didn't create this listing, you can "
            u"safely ignore this email. It was\ncreated by None; please "
            u"contact us if anything seems\nstrange.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team")

        # Verify that the email looks fine.
        self.assertEqual(self.clean(self.emails[0].html),
            u"Welcome to Marketplace Marketplace Hello there, and welcome to "
            u"Marketplace! Your listing has been created. Please click the "
            u"button below to edit it. Edit \"Listing \u2606A\" Important: "
            u"you'll need to click this link at least once for your "
            u"listing to be viewable by others &mdash; this is to protect "
            u"against spam. If you didn't create this listing, you can "
            u"safely ignore this email. "
            u"It was created by None; please contact us if anything seems "
            u"strange. Cheers, The Marketplace Team")

        # Verify that we were sent a chat message.
        self.assertEqual(self.chats, [{
            "icon_url": u"/_ah/gcs/test.appspot.com/listing-a-small",
            "text": ("Posted by seller-a@uchicago.edu "
                     "(<http://localhost/listing_a?key=a_key|approve>)"),
            "username": u"Listing \u2606A"
        }])

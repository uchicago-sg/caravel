from caravel.storage import config
from caravel.tests import helper
from caravel import model

import unittest
import StringIO
import time
import re

class TestListings(helper.CaravelTestCase):
    def test_search(self):
        # View all listings, in order.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Listing \xe2\x98\x86A $3.10 cars 5h ago Listing "
            "\xe2\x98\x86B $71.10 apartments 2d ago")

        # Listings at an offset.
        self.assertEqual(self.clean(self.get("/?offset=1").data),
            "New Listing Listing \xe2\x98\x86B $71.10 apartments 2d ago")

        # Just a subset of listings.
        self.assertEqual(self.clean(self.get("/?q=body+%E2%98%86a").data),
            "New Listing Listing \xe2\x98\x86A $3.10 cars 5h ago")

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
            "message": u"message\u2606 goes here",
            "csrf_token": self.csrf_token("/listing_b"),
        })

        # Even so, ensure that it seems as though it got through.
        self.assertEqual(self.clean(self.get("/listing_b").data),
            "New Listing Your inquiry has been recorded and is awaiting "
            "moderation. Listing \xe2\x98\x86B apartments Posted 2d ago by "
            "[address hidden] ( sign in to view). Price: $71.10 Body of "
            "\xe2\x98\x86B Contact Seller From Sign in with CNetID or Message")

        # Ensure that no emails have been sent.
        self.assertEqual(self.emails, [])

        # Notify the moderators that something has happened.
        self.get("/_internal/nag_moderators")

        # Ensure that the moderators received the right email.
        self.assertEqual(self.emails[0].to[0], "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            u"1 Inquiries, 0 Listings Pending")

        self.assertEqual(self.emails[0].text,
            u"Greetings,\n"
            u"\n"
            u"Please visit http://localhost/moderation to approve things.\n"
            u"\n"
            u"Inquiries (1):\n"
            u"  Listing \u2606B (buyer@foo.com)\n"
        )
        self.emails.pop(0)

        # Approve the first listing.
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
        self.assertEqual(self.emails[0].text,
            u"Hello again!\n\n"
            u"We've received a new inquiry for Listing \u2606B:\n\n"
            u"  Buyer: buyer@foo.com\n"
            u"  \n"
            u"  message\u2606 goes here\n\n"
            u"Simply reply to this email if you'd like to get in contact.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team"
        )

        # Verify that the right messge HTML was sent.
        self.assertEqual(self.clean(self.emails[0].html),
            u"Marketplace "
            u"Hello again! "
            u"We've received a new inquiry for Listing \u2606B: "
            u"Buyer: buyer@foo.com "
            u"message\u2606 goes here "
            u"Simply reply to this email if you'd like to get in contact. "
            u"Cheers, The Marketplace Team")

    def test_post_inquiry_with_cnetid(self):
        # Submit an inquiry.
        with self.google_apps_user("visitor@uchicago.edu"):
            self.post("/listing_b", data={
                "principal": "buyer@foo.com",
                "message": u"message\u2606 goes here",
                "csrf_token": self.csrf_token("/listing_b"),
            })

            # Ensure that we display a helpful message.
            self.assertEqual(self.clean(self.get("/listing_b").data),
                "New Listing Logged in as visitor@uchicago.edu My Listings "
                "Logout Your inquiry has been sent. Listing \xe2\x98\x86B "
                "apartments Posted 2d ago by seller-b@uchicago.edu . Price: "
                "$71.10 Validated by GOOGLE_APPS. Originally posted by 1.2.3.4 "
                "with mozilla. Body of \xe2\x98\x86B Contact Seller From "
                "visitor@uchicago.edu ( Logout ) Message")

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "seller-b@uchicago.edu")
        self.assertEqual(self.emails[0].reply_to, "visitor@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            u"Re: Marketplace Listing \"Listing \u2606B\"")

        # Verify that the right message text was sent.
        self.assertEqual(self.emails[0].text,
            u"Hello again!\n\n"
            u"We've received a new inquiry for Listing \u2606B:\n\n"
            u"  Buyer: visitor@uchicago.edu\n"
            u"  \n"
            u"  message\u2606 goes here\n\n"
            u"Simply reply to this email if you'd like to get in contact.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team"
        )

        # Verify that the right messge HTML was sent.
        self.assertEqual(self.clean(self.emails[0].html),
            u"Marketplace "
            u"Hello again! "
            u"We've received a new inquiry for Listing \u2606B: "
            u"Buyer: visitor@uchicago.edu "
            u"message\u2606 goes here "
            u"Simply reply to this email if you'd like to get in contact. "
            u"Cheers, The Marketplace Team")

    def test_new_listing(self):
        # Try creating a new listing as an unauthenticated user.
        self.post("/new", data={
            "csrf_token": self.csrf_token("/new"),
            "title": u"Title of \u2606D",
            "body": u"Body of \u2606D",
            "price": "3.441",
            "principal": "seller-d@uchicago.edu",
            "categories": "apartments",
            "uploaded_photos-2-image":
                ("caravel/tests/test-pattern.gif", "t.jpg")
        })

        # Ensure that we get a message indicating that it does not exist.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Your listing is awaiting moderation. We&#39;ll email "
            "you when it&#39;s up. Listing \xe2\x98\x86A $3.10 cars 5h ago "
            "Listing \xe2\x98\x86B $71.10 apartments 2d ago")

        # Ensure that the listing does not exist yet.
        self.assertEqual(self.clean(self.get("/ZZ-ZZ-ZZ").data),
            "404 Not Found Not Found The requested URL was not found on the "
            "server. If you entered the URL manually please check your "
            "spelling and try again.")

        # Ensure that no emails have been sent.
        self.assertEqual(self.emails, [])

        # Approve the first listing.
        with self.google_apps_user("admin@uchicago.edu"):
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedListing.query().get().key.urlsafe(),
            })

        # Listing is now published.
        self.assertEqual(self.clean(self.get("/ZZ-ZZ-ZZ").data),
            "New Listing Title of \xe2\x98\x86D apartments Posted now by "
            "[address hidden] ( sign in to view). Price: $3.44 Body of "
            "\xe2\x98\x86D Contact Seller From Sign in with CNetID or Message")

        # Make sure the picture shows up.
        photos = self.extract_photos(self.get("/ZZ-ZZ-ZZ").data)
        now = photos[1].split("/")[4].split("-")[0]
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-large'.format(now)
        ])

        # Listing shows up in searches.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Title of \xe2\x98\x86D $3.44 apartments now Listing "
            "\xe2\x98\x86A $3.10 cars 5h ago Listing \xe2\x98\x86B $71.10 "
            "apartments 2d ago")

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
                "uploaded_photos-2-image":
                    ("caravel/tests/test-pattern.gif", "t.jpg")
            })

            # Listing is now published.
            self.assertEqual(self.clean(self.get("/ZZ-ZZ-ZZ").data),
                "New Listing Logged in as visitor@uchicago.edu My Listings "
                "Logout Your listing has been created. Title of \xe2\x98\x86D "
                "apartments Posted now by visitor@uchicago.edu . Price: $3.44 "
                "Validated by GOOGLE_APPS. Originally posted by None with . "
                "Body of \xe2\x98\x86D Manage Listing Edit")

        # Make sure the picture shows up.
        photos = self.extract_photos(self.get("/ZZ-ZZ-ZZ").data)
        now = photos[1].split("/")[4].split("-")[0]
        self.assertEquals(photos, [
            '/static/images/logo.jpg',
            '/_ah/gcs/test.appspot.com/{}-ZZ-ZZ-ZZ-large'.format(now)
        ])

        # Listing shows up in searches.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Title of \xe2\x98\x86D $3.44 apartments now Listing "
            "\xe2\x98\x86A $3.10 cars 5h ago Listing \xe2\x98\x86B $71.10 "
            "apartments 2d ago")

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
        self.assertEqual(self.emails[0].text,
            u"Hello there, and welcome to Marketplace!\n\n"
            u"Your listing has been created. Please click the link below to "
            u"edit it.\n\n"
            u"  http://localhost/ZZ-ZZ-ZZ\n\n"
            u"Your listing is published. Any interest expressed through the "
            u"\"Contact Seller\"\nform will come as a follow-up to this "
            u"message. Users with CNetIDs can also\ncontact you directly.\n\n"
            u"Cheers,\n"
            u"The Marketplace Team"
        )

        # Verify that the right messge HTML was sent.
        self.assertEqual(self.clean(self.emails[0].html),
            u"Marketplace "
            u"Hello there, and welcome to Marketplace! "
            u"Your listing has been created. Please click the button below to "
            u"edit it. "
            u"Edit \"Title of \u2606D\" "
            u"Your listing is published. Any interest expressed through the "
            u"\"Contact Seller\" form will come as a follow-up to this "
            u"message. Users with CNetIDs can also contact you directly. "
            u"Cheers, "
            u"The Marketplace Team"
        )

    def test_edit_listing(self):
        # Try editing someone else's listing.
        result = self.post("/listing_a/edit", data=dict(
            csrf_token=self.csrf_token("/listing_a/edit"),
            title=u"Title\u2606A",
            body=u"Body\u2606A",
            price="2.34",
            principal="seller-a@uchicago.edu",
            categories="cars",
        )).data

        self.assertEqual(self.clean(result),
            "New Listing Title Seller Sign in with CNetID or Please sign in "
            "with your CNetID. BSD/Medicine/Medical School affiliates: if "
            "you are unable to sign in with your CNetID, please enter your "
            "email in the box. Your listing might not be posted immediately. "
            "We reserve the right to remove listings at any time. Categories "
            "Apartments Subleases Appliances Bikes Books Cars Electronics "
            "Employment Furniture Miscellaneous Services Wanted Price Body "
            "Body\xe2\x98\x86A Image Image Image Image Image Cancel"
        )

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

            self.assertEqual(self.clean(self.get("/listing_a").data),
                "New Listing Logged in as seller-a@uchicago.edu My Listings "
                "Logout Your listing has been updated. Title\xe2\x98\x86A cars "
                "Posted now by seller-a@uchicago.edu . Price: $2.34 Validated "
                "by GOOGLE_APPS. Originally posted by None with . "
                "Body\xe2\x98\x86A Manage Listing Edit"
            )

    @unittest.skip("Claim listing features disabled")
    def test_claim_listing(self):
        # View a listing and click "Claim"
        result = self.post("/listing_a/claim", data=dict(
            csrf_token=self.csrf_token("/listing_a")
        ))

        # Ensure that the flash shows up.
        self.assertEqual(self.clean(self.get("/listing_a").data),
            "New Listing We&#39;ve emailed you a link to edit this listing. "
            "Listing \xe2\x98\x86A Cars $3.10 Body of \xe2\x98\x86A Contact "
            "Seller Email Sign in with CNetID or Message")

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

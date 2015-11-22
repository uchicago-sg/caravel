from caravel.storage import entities, config
from caravel.tests import helper

import time
import re

class TestListings(helper.CaravelTestCase):
    def test_search(self):
        # View all listings, in order.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Listing tA 5h ago Cars $3.10 Listing tB 2d ago "
            "Apartments $71.10")

        # Listings at an offset.
        self.assertEqual(self.clean(self.get("/?offset=1").data),
            "New Listing Listing tB 2d ago Apartments $71.10")

        # Just a subset of listings.
        self.assertEqual(self.clean(self.get("/?q=body+ta").data),
            "New Listing Listing tA 5h ago Cars $3.10")

        # Make sure links work.
        self.assertIn("/listing_a", self.get("/?q=body+ta").data)

    def test_inquiry(self):
        # Submit an inquiry.
        self.post("/listing_b", data=dict(
            buyer="buyer@foo.com",
            message="message goes here",
            csrf_token=self.csrf_token("/listing_b"),
        ))

        # Verify that the UI is updated.
        self.assertEqual(self.clean(self.get("/listing_b").data),
            "New Listing Your inquiry has been sent. Listing tB Apartments "
            "$71.10 Body of bB Contact Seller This listing has 1 inqury. Email "
            "UChicago Email Preferred Message")

        # Verify that the proper email was sent.
        self.assertEqual(self.emails[0].to[0], "seller-b@uchicago.edu")
        self.assertEqual(self.emails[0].reply_to, "buyer@foo.com")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            "Re: Marketplace Listing \"Listing tB\"")

        # Verify that the right message text was sent.
        self.assertEqual(self.emails[0].text,
            "Hello again!\n\n"
            "We've received a new inquiry for Listing tB:\n\n"
            "  Buyer: buyer@foo.com (IP: None)\n"
            "  \n"
            "  message goes here\n\n"
            "Simply reply to this email if you'd like to get in contact.\n\n"
            "Cheers,\n"
            "The Marketplace Team"
        )

        # Verify that the right messge HTML was sent.
        self.assertEqual(self.clean(self.emails[0].html),
            "My Test Email Marketplace Hello again! We've received a new "
            "inquiry for Listing tB: Buyer: buyer@foo.com (IP: None) message "
            "goes here Simply reply to this email if you'd like to get in "
            "contact. Cheers, The Marketplace Team")

    def test_new_listing(self):
        # Try creating a new listing as an authenticated user.
        self.post("/new", data=dict(
            csrf_token=self.csrf_token("/new"),
            title="Listing tD",
            description="Listing bD",
            seller="seller-d@uchicago.edu",
            categories="category:books"
        ))

        # Verify that the listing does not exist yet.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Your listing has been created. Click the link in "
            "your email to publish it. Listing tA 5h ago Cars $3.10 Listing "
            "tB 2d ago Apartments $71.10")

        # Ensure that we were sent a link to edit a listing.
        self.assertEqual(self.emails[0].to[0], "seller-d@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            "Marketplace Listing \"Listing tD\"")

        self.assertEqual(self.emails[0].text,
            "Hello there, and welcome to Marketplace!\n\n"
            "Your listing has been created. Please click the link below "
            "to edit it.\n\n"
            "  http://localhost/ZZ-ZZ-ZZ?key=ZZ-ZZ-ZZ\n\n"
            "Important: you'll need to click this link at least once for "
            "your listing to\nbe viewable by others -- this is to protect "
            "against spam.\n\nIf you didn't create this listing, you can "
            "safely ignore this email. It was\ncreated by None; please contact "
            "us if anything seems\nstrange.\n\n"
            "Cheers,\n"
            "The Marketplace Team")

        # Verify that the email looks fine.
        self.assertEqual(self.clean(self.emails[0].html),
            "Welcome to Marketplace Marketplace Hello there, and welcome to "
            "Marketplace! Your listing has been created. Please click the "
            "button below to edit it. Edit \"Listing tD\" Important: you'll "
            "need to click this link at least once for your listing to be "
            "viewable by others &mdash; this is to protect against spam. If "
            "you didn't create this listing, you can safely ignore this email. "
            "It was created by None; please contact us if anything seems "
            "strange. Cheers, The Marketplace Team")

        # Click the link in the message.
        page = self.get("/ZZ-ZZ-ZZ?key=ZZ-ZZ-ZZ")

        # Listing is now published.
        self.assertEqual(self.clean(self.get("/ZZ-ZZ-ZZ").data),
            "New Listing Logged in as seller-d@uchicago.edu My Listings Logout "
            "Your listing has been published. Listing tD Books $0.00 Listing "
            "bD Manage Listing Edit")

        # Listing shows up in searches.
        self.assertEqual(self.clean(self.get("/").data),
            "New Listing Logged in as seller-d@uchicago.edu My Listings Logout "
            "Listing tD now ago Books $0.00 Listing tA 5h ago Cars $3.10 "
            "Listing tB 2d ago Apartments $71.10")

    def test_claim_listing(self):
        # View a listing and click "Claim"
        self.post("/listing_a/claim", data=dict(
            csrf_token=self.csrf_token("/listing_a")
        ))

        # Ensure that the flash shows up.
        self.assertEqual(self.clean(self.get("/listing_a").data),
            "New Listing We&#39;ve emailed you a link to edit this listing. "
            "Listing tA Cars $3.10 Body of bA Contact Seller Email UChicago "
            "Email Preferred Message")

        # Ensure that the message is as we expect.
        self.assertEqual(self.emails[0].to[0], "seller-a@uchicago.edu")
        self.assertEqual(self.emails[0].from_email,
            "marketplace@lists.uchicago.edu")
        self.assertEqual(self.emails[0].subject,
            "Marketplace Listing \"Listing tA\"")

        # Verify the textual contents of the message.
        self.assertEqual(self.emails[0].text,
            "Hello there, and welcome to Marketplace!\n\n"
            "Your listing has been created. Please click the link below "
            "to edit it.\n\n"
            "  http://localhost/listing_a?key=a_key\n\n"
            "Important: you'll need to click this link at least once for "
            "your listing to\nbe viewable by others -- this is to protect "
            "against spam.\n\nIf you didn't create this listing, you can "
            "safely ignore this email. It was\ncreated by None; please contact "
            "us if anything seems\nstrange.\n\n"
            "Cheers,\n"
            "The Marketplace Team")

        # Verify that the email looks fine.
        self.assertEqual(self.clean(self.emails[0].html),
            "Welcome to Marketplace Marketplace Hello there, and welcome to "
            "Marketplace! Your listing has been created. Please click the "
            "button below to edit it. Edit \"Listing tA\" Important: you'll "
            "need to click this link at least once for your listing to be "
            "viewable by others &mdash; this is to protect against spam. If "
            "you didn't create this listing, you can safely ignore this email. "
            "It was created by None; please contact us if anything seems "
            "strange. Cheers, The Marketplace Team")

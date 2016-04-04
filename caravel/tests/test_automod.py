from caravel import model

from caravel.tests import helper


class TestAutomaticModeration(helper.CaravelTestCase):

    def test_control_panel(self):
        # Post a new listing.
        self.post("/listing_b", data={
            "principal": "buyer@foo.com",
            "message": u"message\u2606 goes here",
            "csrf_token": self.csrf_token("/listing_b"),
        })

        # Post an inquiry.
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

        with self.google_apps_user("foo@uchicago.edu"):
            self.assertLongString(self.get("/moderation").data)

            # Approve the inquiry
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedListing.query().get().key.urlsafe(),
            })

            self.assertLongString(self.get("/moderation").data)

            # Approve the listing.
            self.post("/moderation", data={
                "csrf_token": self.ajax_csrf_token("/moderation"),
                "approve": model.UnapprovedInquiry.query().get().key.urlsafe(),
            })

            self.assertLongString(self.get("/moderation").data)

    def test_automod(self):
        # Post a new inqury.
        self.post("/listing_b", data={
            "principal": "buyer@foo.com",
            "message": u"message\u2606 goes here",
            "csrf_token": self.csrf_token("/listing_b"),
        })

        # Post some fraud.
        self.post("/new", data={
            "csrf_token": self.csrf_token("/new"),
            "title": u"Title of \u2606D",
            "body": u"Body of \u2606D",
            "price": "3.441",
            "principal": "marycole396@yahoo.com",
            "categories": "apartments",
            "uploaded_photos-2-image":
                ("caravel/tests/test-pattern.gif", "t.jpg")
        })

        self.assertEquals(1, len(list(model.UnapprovedListing().query())))
        self.assertEquals(1, len(list(model.UnapprovedInquiry().query())))

        # Clear flash messages.
        self.get("/")

        with self.google_apps_user("admin@uchicago.edu"):
            # By default, automod does nothing.
            self.get("/_internal/automod")
            self.assertEquals(self.emails, [])
            self.assertLongString(self.get("/moderation").data)

            # But if enabled, it approves just the inquiry.
            self.post("/moderation", data={
                "csrf_token": self.csrf_token("/moderation"),
                "automod": "true"
            })

            self.post("/moderation", data={
                "csrf_token": self.csrf_token("/moderation"),
                "automod": "true",
                "blacklist": "^marycole.*",
                "min_delay": "0",
            })

            # When configured, automod approves the first one
            self.get("/_internal/automod")
            self.assertEquals(len(self.emails), 1)

            # If configured more openly, it approves all.
            self.post("/moderation", data={
                "csrf_token": self.csrf_token("/moderation"),
                "automod": "true",
                "blacklist": "",
                "min_delay": "0",
            })

            self.get("/_internal/automod")
            self.assertEquals(len(self.emails), 2)

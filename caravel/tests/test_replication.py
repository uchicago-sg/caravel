from caravel.tests import helper
from caravel import model
import json


class TestListings(helper.CaravelTestCase):

    def test_creation(self):
        # Submit an inquiry.
        with self.google_apps_user("visitor@uchicago.edu"):
            self.post("/listing_b", data={
                "principal": "buyer@foo.com",
                "message": u"message\u2606 goes here",
                "csrf_token": self.csrf_token("/listing_b"),
            })

        self.assertEquals(
            [(u, json.loads(d)) for u, d in self.webhooks],
            [
                ("https://go-marketplace.appspot.com/listings",
                 {u"replication_key": u"~key~",
                  u"key": u"listing_a",
                  u"title": u"Listing \u2606A",
                  u"sold": False,
                  u"body": u"Body of \u2606A",
                  u"categories": [u"cars"],
                  u"photos": [
                      {u"large": u"/_ah/gcs/test.appspot.com/listing-a-large",
                       u"small": u"/_ah/gcs/test.appspot.com/listing-a-small"},
                      {u"large": u"/_ah/gcs/test.appspot.com/listing-a2-large",
                       u"small": u"/_ah/gcs/test.appspot.com/listing-a2-small"}
                  ],
                  u"posted_at": self.listing_a.posted_at.isoformat(),
                  u"price": 3.1,
                  u"seller": {
                      u"email": u"seller-a@uchicago.edu",
                      u"validated": True},
                  u"moderated": True}),
                ("https://go-marketplace.appspot.com/listings",
                 {u"replication_key": u"~key~",
                  u"key": u"listing_b",
                  u"title": u"Listing \u2606B",
                  u"sold": False,
                  u"body": u"Body of \u2606B",
                  u"categories": [u"apartments"],
                  u"photos": [
                      {u"large": u"/_ah/gcs/test.appspot.com/listing-b-large",
                       u"small": u"/_ah/gcs/test.appspot.com/listing-b-small"},
                      {u"large": u"/_ah/gcs/test.appspot.com/listing-b2-large",
                       u"small": u"/_ah/gcs/test.appspot.com/listing-b2-small"}
                  ],
                  u"posted_at": self.listing_b.posted_at.isoformat(),
                  u"price": 71.1,
                  u"seller": {
                      u"email": u"seller-b@uchicago.edu",
                      u"validated": False},
                  u"moderated": True}),
                ("https://go-marketplace.appspot.com/inquiries",
                 {u"key": 11,
                  u"listing": "listing_b",
                  u"message": u"message\u2606 goes here",
                  u"moderated": True,
                  u"replication_key": u"~key~",
                  u"sender": {
                      u"email": u"visitor@uchicago.edu", u"validated": True}
                  })
            ])

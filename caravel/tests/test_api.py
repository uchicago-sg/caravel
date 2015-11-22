import json

from caravel.storage import entities, config
from caravel.tests import helper

class TestListings(helper.CaravelTestCase):
    def test_read_api(self):
        cars = {
            u"URL":
            u"http://localhost/api/v1/listings.json?q=category%3Acars",
            u"name": u"category:cars"
        }
    
        apartments = {
            u"URL":
            u"http://localhost/api/v1/listings.json?q=category%3Aapartments",
            u"name": u"category:apartments"
        }

        listing_a = {
            u"body": u"Body of bA",
            u"categories": [cars],
            u"photos": [],
            u"htmlURL": u"http://localhost/listing_a",
            u"inquiries": 0,
            u"jsonURL": u"http://localhost/api/v1/listing_a.json",
            u"postingTime": self.listing_a.posting_time,
            u"price": 3.1,
            u"title": u"Listing tA"
        }

        listing_b = {
            u"body": u"Body of bB",
            u"categories": [apartments],
            u"photos": [],
            u"htmlURL": u"http://localhost/listing_b",
            u"inquiries": 0,
            u"jsonURL": u"http://localhost/api/v1/listing_b.json",
            u"postingTime": self.listing_b.posting_time,
            u"price": 71.1,
            u"title": u"Listing tB"
        }

        # Try to retreive all listings.
        self.assertEquals(
            json.loads(self.get("/api/v1/listings.json").data),
            {
                u"limit": 100,
                u"offset": 0,
                u"listings": [listing_a, listing_b],
            }
        )

        self.assertEquals(
            json.loads(self.get("/api/v1/listings.json?offset=1").data),
            {
                u"limit": 100,
                u"offset": 1,
                u"listings": [listing_b],
                u"previousURL":
                    u"http://localhost/api/v1/listings.json?offset=0"
            }
        )

        self.assertEquals(
            json.loads(self.get("/api/v1/listings.json?limit=1").data),
            {
                u"limit": 1,
                u"offset": 0,
                u"listings": [listing_a],
                u"nextURL": u"http://localhost/api/v1/listings.json?offset=1"
            }
        )

        # Check that one listing appears is as it should be.
        self.assertEquals(
            json.loads(self.get("/api/v1/listing_a.json").data), listing_a)
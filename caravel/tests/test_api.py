import json
import unittest
import calendar

from caravel.storage import config
from caravel.tests import helper

class TestListings(helper.CaravelTestCase):
     def test_read_api(self):
        cars = {
            u"URL":
            u"http://localhost/api/v1/listings.json?q=category%3Acars",
            u"name": u"cars"
        }
    
        apartments = {
            u"URL":
            u"http://localhost/api/v1/listings.json?q=category%3Aapartments",
            u"name": u"apartments"
        }

        listing_a = {
            u"body": u"Body of \u2606A",
            u"categories": [cars],
            u"htmlURL": u"http://localhost/listing_a",
            u"jsonURL": u"http://localhost/api/v1/listing_a.json",
            u"postingTime": calendar.timegm(
                self.listing_a.posted_at.timetuple()),
            u"price": 3.1,
            u"title": u"Listing \u2606A",
            u"photos": [
                {u"large": u"/_ah/gcs/test.appspot.com/listing-a-large",
                 u"small": u"/_ah/gcs/test.appspot.com/listing-a-small"},
                {u"large": u"/_ah/gcs/test.appspot.com/listing-a2-large",
                 u"small": u"/_ah/gcs/test.appspot.com/listing-a2-small"}],
        }

        listing_b = {
            u"body": u"Body of \u2606B",
            u"categories": [apartments],
            u"htmlURL": u"http://localhost/listing_b",
            u"jsonURL": u"http://localhost/api/v1/listing_b.json",
            u"postingTime": calendar.timegm(
                self.listing_b.posted_at.timetuple()),
            u"price": 71.1,
            u"title": u"Listing \u2606B",
            u"photos": [
                {u"large": u"/_ah/gcs/test.appspot.com/listing-b-large",
                 u"small": u"/_ah/gcs/test.appspot.com/listing-b-small"},
                {u"large": u"/_ah/gcs/test.appspot.com/listing-b2-large",
                 u"small": u"/_ah/gcs/test.appspot.com/listing-b2-small"}],
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

        # self.assertEquals(
        #     json.loads(self.get("/api/v1/listings.json?offset=1").data),
        #     {
        #         u"limit": 100,
        #         u"offset": 1,
        #         u"listings": [listing_b],
        #         u"previousURL":
        #             u"http://localhost/api/v1/listings.json?offset=0"
        #     }
        # )
        #
        # self.assertEquals(
        #     json.loads(self.get("/api/v1/listings.json?limit=1").data),
        #     {
        #         u"limit": 1,
        #         u"offset": 0,
        #         u"listings": [listing_a],
        #         u"nextURL": u"http://localhost/api/v1/listings.json?offset=1"
        #     }
        # )

        # Check that one listing appears is as it should be.
        self.assertEquals(
            json.loads(self.get("/api/v1/listing_a.json").data), listing_a)
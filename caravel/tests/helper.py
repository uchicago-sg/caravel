import unittest
import time
import re
import uuid

from google.appengine.ext import db
from google.appengine.api import memcache

from caravel import app
from caravel.storage import config, entities

class CaravelTestCase(unittest.TestCase):
    def setUp(self):
        # FIXME: Remove once everything else is TestCase-ified.
        db.delete(db.Query(keys_only=True))
        memcache.flush_all()

        # Configure a basic HTTP client.
        self.http_client = app.test_client()

        # Capture outgoing email messages.
        self.emails = []
        sendgrid = config.send_grid_client
        self._send, sendgrid.send = sendgrid.send, self.emails.append

        # Ensure that UUIDs are deterministic.
        self._uuid4 = uuid.uuid4
        uuid.uuid4 = lambda: "ZZ-ZZ-ZZ"

        # Create simple entities to play with.
        self.listing_a = entities.Listing(
            title="Listing tA",
            body="Body of bA",
            posting_time=time.time() - 4 * 3600,
            seller="seller-a@uchicago.edu",
            price=310,
            categories=["category:cars"],
            admin_key="a_key",
            key_name="listing_a")
        self.listing_a.put()

        self.listing_b = entities.Listing(
            title="Listing tB",
            body="Body of bB",
            posting_time=time.time() - 24 * 3600,
            seller="seller-b@uchicago.edu",
            price=7110,
            categories=["category:apartments"],
            key_name="listing_b")
        self.listing_b.put()
        
        self.listing_c = entities.Listing(
            title="Listing tC",
            body="Body of bC",
            posting_time=0.,
            seller="seller-c@uchicago.edu",
            price=9105,
            categories=["category:appliances"],
            admin_key="adminkey",
            key_name="listing_c")
        self.listing_c.put()

        # Allow very large diffs.
        self.maxDiff = None

    def tearDown(self):
        # Clear database.
        db.delete(db.Query(keys_only=True))
        memcache.flush_all()

        # Un-stub uuid generation features.
        uuid.uuid4 = self._uuid4
        config.send_grid_client.send = self._send

    # Test helper functions.
    def clean(self, markup):
        markup = re.sub(r'<script.*/script>', ' ', markup, flags=re.DOTALL)
        markup = re.sub(r'<!--.*-->', '', markup, flags=re.DOTALL)
        markup = re.sub(r'<[^>]+>', ' ', markup)
        markup = re.sub(r'[ \t\r\n]+', ' ', markup)
        markup = re.sub(r'Marketplace is.*lists.uchicago.edu\. ', '', markup)
        markup = re.sub(r'(^.*UChicago Marketplace)|(&#169;.*$)', '', markup)
        return markup.strip()

    def csrf_token(self, url):
        return re.search(r'csrf_token".*"(.*)"', self.get(url).data).group(1)

    def get(self, *vargs, **kwargs):
        return self.http_client.get(*vargs, **kwargs)

    def post(self, *vargs, **kwargs):
        return self.http_client.post(*vargs, **kwargs)
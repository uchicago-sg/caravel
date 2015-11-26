from google.appengine.api import memcache
from caravel.storage import dos
from caravel.tests import helper
import time
import uuid

class TestListings(helper.CaravelTestCase):
    def test_rate_limit(self):
        trace = []

        # Post a bunch.
        with self.current_time(0):
            for i in xrange(5):
                trace.append(dos.rate_limit("key", 3, 60))

        # Pause, then post some more.
        with self.current_time(100):
            for i in xrange(2):
                trace.append(dos.rate_limit("key", 3, 60))

        self.assertEquals(trace, [
            False, False, False, True, True, False, False])

    def test_posting_limit(self):
        # Try to create lots of listings.
        created = 0
        for i in xrange(7):
            # FIXME: Find a smarter way to generate deterministic unique IDs.
            uuid.uuid4 = lambda: "U{}".format(i)
            if self.post("/new", data=dict(
                title="test listing",
                description="body goes here",
                categories="category:books",
                seller="foobar@uchicago.edu",
                csrf_token=self.csrf_token("/new")
            )).status == "302 FOUND":
                created += 1

        # Ensure that only four listings were created.
        self.assertEquals(created, 4)
        self.assertEquals(len(self.emails), 4)

    def test_claim_listing(self):
        # Try to spam the "Claim Listing" button.
        for i in xrange(10):
            self.post("/listing_a/claim", data=dict(
                csrf_token=self.csrf_token("/listing_a")
            ))

        # Make sure we only get one message.
        self.assertEquals(len(self.emails), 1)

    def test_send_inquiry(self):
        # Try to spam the "Inquire About Listing" button.
        for i in xrange(10):
            self.post("/listing_a", data=dict(
                message="hello there",
                buyer="foo+{}@uchicago.edu".format(i),
                csrf_token=self.csrf_token("/listing_a")
            ))

        # Make sure we only get a few messages.
        self.assertEquals(len(self.emails), 4)

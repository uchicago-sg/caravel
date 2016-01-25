import unittest
import datetime
import re
import uuid
import time
import sys
import os
from contextlib import contextmanager

from google.appengine.ext import db
from google.appengine.api import memcache, users

from caravel import app, model, utils
from caravel.storage import config


class OutOfContextLiteralsMixin(unittest.TestCase):

    """
    Uses an outside file to store long string literals.
    """

    def assertLongString(self, x, _=None):
        """
        Asserts that the given long string is at it should be.
        """

        x = self.clean(x)
        if isinstance(x, unicode):
            x = x.encode('utf-8')

        if self.generating_asserts:
            self.expectations.append(x)
        else:
            self.assertEquals(x.split("\n"),
                              self.expectations.pop(0).split("\n"))

    def setUp(self):
        """
        Loads the expectations for this TestCase.
        """

        base = sys.modules[self.__class__.__module__].__file__
        base = re.sub(r'.[^.]+$', '', base)
        method_name = re.sub(r'^test_', '', self.id().split('.')[-1])

        self.expect_file = '{}_{}_expect.txt'.format(base, method_name)
        try:
            self.expectations = open(self.expect_file).read().split("\n---\n")
        except:
            self.expectations, self.generating_asserts = [], True
        else:
            self.generating_asserts = False

    def tearDown(self):
        """
        Saves the expectations into the asserts file.
        """

        if self.generating_asserts:
            with open(self.expect_file, "w") as fp:
                fp.write("\n---\n".join(self.expectations))

    def clean(self, markup):
        """
        De-HTML-ifies the given string so that it can be read in a text file.
        """

        if not isinstance(markup, basestring):
            raise ValueError("{!r} is not a basestring".format(markup))

        markup = re.sub(r'<script.*?/script>', ' ', markup, flags=re.DOTALL)
        markup = re.sub(r'<!--.*-->', '', markup, flags=re.DOTALL)
        markup = re.sub(r'<[^>]+>', ' ', markup)
        markup = re.sub(r'[ \t]+', ' ', markup)
        markup = "\n".join(l.strip() for l in markup.split("\n") if l.strip())
        markup = re.sub(r'Marketplace is.*lists\.uchicago\.edu\.\n', '',
                        markup, flags=re.DOTALL)
        return markup


class CaravelTestCase(OutOfContextLiteralsMixin, unittest.TestCase):

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

        # Capture outgoing Slack messages.
        # self.chats = []
        # self._send_chat = slack.send_chat
        # slack.send_chat = lambda **kw: self.chats.append(kw)

        # Ensure that UUIDs are deterministic.
        self._uuid4 = uuid.uuid4
        uuid.uuid4 = lambda: "ZZ-ZZ-ZZ"

        # Allocate a test session.
        device = utils.Device(
            nonce="foobar",
            user_agent="mozilla",
            ip_address="1.2.3.4"
        )

        # Create simple entities to play with.
        self.listing_a = model.Listing(
            title=u"Listing \u2606A",
            body=u"Body of \u2606A",
            posted_at=datetime.datetime.now() - datetime.timedelta(hours=4),
            principal=utils.Principal("seller-a@uchicago.edu", device,
                                      utils.Principal.GOOGLE_APPS),
            run_trigger=True,
            version=11,
            price=3.10,
            categories=["cars"],
            photos=[model.Photo("listing-a"), model.Photo("listing-a2")],
            id="listing_a")
        self.listing_a.put()

        seller_b = utils.Principal("seller-b@uchicago.edu", device,
                                   utils.Principal.EMAIL)
        seller_b.validated_by = "fixture for unit test"

        self.listing_b = model.Listing(
            title=u"Listing \u2606B",
            body=u"Body of \u2606B",
            posted_at=datetime.datetime.now() - datetime.timedelta(hours=24),
            principal=seller_b,
            price=71.10,
            run_trigger=True,
            version=11,
            categories=["apartments"],
            photos=[model.Photo("listing-b"), model.Photo("listing-b2")],
            id="listing_b")
        self.listing_b.put()

        # Allow very large diffs.
        self.maxDiff = None

        # Look up static expectations.
        super(CaravelTestCase, self).setUp()

    def tearDown(self):
        # Clear database.
        db.delete(db.Query(keys_only=True))
        memcache.flush_all()

        # Un-stub mocks.
        uuid.uuid4 = self._uuid4
        config.send_grid_client.send = self._send
        # slack.send_chat = self._send_chat

        super(CaravelTestCase, self).tearDown()

    # Test helper functions.
    def clean(self, markup):
        """
        Add certain Marketplace-specific filters.
        """

        markup = super(CaravelTestCase, self).clean(markup)
        markup = re.sub(r'(^.*UChicago Marketplace)|(&#169;.*$)', '', markup,
                        flags=re.DOTALL)
        markup = re.sub(r'Please .* Update to Marketplace \.\n', '', markup,
                        flags=re.DOTALL)
        markup = re.sub(r'tip: .*? listings\n', '', markup, flags=re.DOTALL)
        markup = re.sub(r'Alumni/BSD.*?any time\. ', '', markup,
                        flags=re.DOTALL)
        return markup.strip()

    def extract_photos(self, markup):
        return re.findall(r'<img[ \t]+src="([^"]+)"', markup)

    def ajax_csrf_token(self, url):
        return re.search(r'Moderation\("(.*)"\)', self.get(url).data).group(1)

    def csrf_token(self, url):
        return re.search(r'csrf_token".*"(.*)"', self.get(url).data).group(1)

    def get(self, *vargs, **kwargs):
        return self.http_client.get(*vargs, **kwargs)

    def post(self, *vargs, **kwargs):
        return self.http_client.post(*vargs, **kwargs)

    @contextmanager
    def google_apps_user(self, email, is_admin=True):
        class FakeUser():

            def email(self):
                return email

        _current_user = users.get_current_user
        users.get_current_user = lambda: FakeUser()

        _is_admin = users.is_current_user_admin
        users.is_current_user_admin = lambda: is_admin

        try:
            yield
        finally:
            users.get_current_user = _current_user
            users.is_current_user_admin = _is_admin

    @contextmanager
    def current_time(self, now):
        _time, time.time = time.time, lambda: now

        try:
            yield
        finally:
            time.time = _time

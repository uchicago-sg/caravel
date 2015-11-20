from caravel import app
from caravel.storage import entities, config
import time
import re


def test_search():
    entities.Listing(
        title="integtesta", posting_time=time.time() - 35000,
        key_name="test_listing_search").put()

    client = app.test_client()
    page = client.get("/?q=integtesta")

    assert "integtesta" in page.data
    assert "10h ago" in page.data
    assert "$0.00" in page.data
    assert "/test_listing_search" in page.data

    page = client.get("/?q=integtesta&offset=1")
    assert "test_listing_search" not in page.data

def test_show():
    entities.Listing(title="integtestb", body="integbody", admin_key="4",
                     key_name="listingb", seller="e@mail").put()

    client = app.test_client()
    page = client.get("/listingb")

    assert page.status == "404 NOT FOUND"

    client.get("/listingb?key=4")
    page = client.get("/listingb")

    assert "e@mail" in page.data
    assert "integtestb" in page.data
    assert "integbody" in page.data


def test_inquiry():
    entities.Listing(title="integtestb", posting_time=1.,
                     key_name="listingc", seller="seller@foo.com").put()

    emails = []
    client = config.send_grid_client
    _send, client.send = client.send, emails.append

    try:
        client = app.test_client()
        page = client.get("/listingc")
        csrf_token = re.search(r'csrf_token".*"(.*)"', page.data).group(1)

        page = client.post("/listingc", data=dict(
            buyer="buyer@foo.com",
            message="message goes here",
            csrf_token=csrf_token,
        ))

        assert len(emails) == 1

        assert emails[0].to[0] == "seller@foo.com"
        assert emails[0].reply_to == "buyer@foo.com"

        assert "integtestb" in emails[0].html
        assert "buyer@foo.com" in emails[0].html
        assert "message goes here" in emails[0].html

        assert "integtestb" in emails[0].text
        assert "buyer@foo.com" in emails[0].text
        assert "message goes here" in emails[0].text

    finally:
        client.send = _send


def test_new_listing():
    emails = []
    client = config.send_grid_client
    _send, client.send = client.send, emails.append

    try:
        client = app.test_client()
        page = client.get("/new")
        csrf_token = re.search(r'csrf_token".*"(.*)"', page.data).group(1)

        page = client.post("new", data=dict(
            csrf_token=csrf_token,
            title="thenewlisting",
            description="foobar",
            seller="foo@uchicago.edu",
            categories="books"
        ))

        assert page.status == "302 FOUND"
        assert len(emails) == 1

        assert emails[0].to[0] == "foo@uchicago.edu"
        assert emails[0].from_email == "marketplace@lists.uchicago.edu"

        assert "thenewlisting" in emails[0].html

        path = re.search(r'http://localhost(/.*)"', emails[0].html).group(1)
        client.get(path).data  # create listing
        assert "thenewlisting" in client.get(path).data

        path2 = re.search(r'http://localhost(/.*)', emails[0].text).group(1)
        assert path2 == path

    finally:
        client.send = _send

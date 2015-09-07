import urlparse, os
from caravel import app
from caravel.daemons import migration
from caravel.storage import helpers
from flask import jsonify

if not os.environ["SERVER_SOFTWARE"].startswith("Development/"):
    raise ImportError("You should not import integration_test in production.")

@app.route("/_integration_test")
def run_integration_test():
    """Ensures that this version of Marketplace mostly works."""

    def opener(url):
        """Stub to map network activity to a local directory."""
        path = "{}/fixtures{}".format(os.path.dirname(__file__),
                                      urlparse.urlparse(url).path)
        return open(path)

    # Migrate a listing from the old site.
    migration.pull_from_listing("listing-a", _urlopen=opener)

    # Verify that the listing was created.
    data = helpers.lookup_listing("listing-a")
    if (data["key"] != "listing-a" or
        data["title"] != "my fancy sublet" or
        data["body"] != "description here" or
        data["price"] != 123456 or
        len(data["photos"]) != 2 or
        data["posting_time"] != 1441609780.0 or
        data["seller"] != "seller@uchicago.edu"):

        raise ValueError("migration failed")

    print "Everything worked!"

    return "ok"
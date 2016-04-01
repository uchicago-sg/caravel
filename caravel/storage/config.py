"""
The config module holds a few scalars that seldom change but cannot exist in the
source code.
"""

import os
import base64
from google.appengine.ext import db
from caravel import app
from flask_bootstrap import Bootstrap
import sendgrid


class Parameter(db.Model):

    """A parameter is a constant value that is set by default."""
    value = db.StringProperty()


def lookup(key, default):
    """Look up the given key, or return the default."""
    return Parameter.get_or_insert(key_name=key, value=default).value


def get_tor_addresses():
    return []

send_grid_client = sendgrid.SendGridClient(lookup("sendgrid_client", ""))
app.secret_key = lookup(
    "session_secret",
    base64.b64encode(
        os.urandom(32))) or os.urandom(32)
slack_url = lookup("slack_url", "")
app.config["RECAPTCHA_PUBLIC_KEY"] = lookup(
    "recaptcha_public_key",
    "6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI")
app.config["RECAPTCHA_PRIVATE_KEY"] = lookup(
    "recaptcha_private_key",
    "6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe")
app.config["RECAPTCHA_DATA_ATTRS"] = {"size": "compact"}
replication_key = lookup("replication_key", "~key~")

Bootstrap(app)

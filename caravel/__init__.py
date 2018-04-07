"""
Caravel is an open source marketplace; it powers //marketplace.uchicago.edu.
Please see README.md for details.
"""

import sys
import os
import logging
sys.path[:0] = [os.path.dirname(__file__) + "/../vendor"]

from flask import Flask
app = Flask(__name__)

if "APPLICATION_ID" not in os.environ:
    os.environ["APPLICATION_ID"] = "dev~test"

    # Hide all the App Engine cruft.
    logging.disable(logging.INFO)

    from google.appengine.ext import testbed, ndb
    testbed = testbed.Testbed()
    testbed.activate()
    testbed.init_all_stubs()
    ndb.get_context().set_cache_policy(False)
    app.testing = True

# Ensure that the Recaptcha field is small.
app.config["RECAPTCHA_DATA_ATTRS"] = {"size": "compact"}

# Enable global CSRF protection.
from flask_wtf.csrf import CsrfProtect
CsrfProtect(app)

# Imported for side effects:
import caravel.storage.config
import caravel.controllers.listings
import caravel.controllers.api
import caravel.controllers.moderation
import caravel.daemons.migration
import caravel.daemons.delete_old_photos
import caravel.daemons.nag_moderators

"""
Caravel is an open source marketplace; it powers //marketplace.uchicago.edu.
Please see README.md for details.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__) + "/../vendor")

from flask import Flask
app = Flask(__name__)

if "APPLICATION_ID" not in os.environ:
    os.environ["APPLICATION_ID"] = "dev~test"
    from google.appengine.ext import testbed
    testbed = testbed.Testbed()
    testbed.activate()
    testbed.init_all_stubs()
    app.testing = True

app.config["RECAPTCHA_DATA_ATTRS"] = {"size": "compact"}

# Imported for side effects:
from caravel.storage import config, photos
from caravel.controllers import listings, api
from caravel.daemons import replication, migration, delete_old_photos
from caravel import utils

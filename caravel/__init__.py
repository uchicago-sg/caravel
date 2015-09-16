"""
Caravel is an open source marketplace; it powers //marketplace.uchicago.edu.
Please see README.md for details.
"""

import sys, os
sys.path.append(os.path.dirname(__file__) + "/../vendor")

from flask import Flask
app = Flask(__name__)

# Imported for side effects:
from caravel.storage import config, photos
from caravel.controllers import listings
from caravel.daemons import replication, migration

# Import test modules iff running locally.
if os.environ["SERVER_SOFTWARE"].startswith("Development/"):
    from caravel.testing import integration_test

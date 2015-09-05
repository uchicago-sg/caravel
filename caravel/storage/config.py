"""
The config module holds a few scalars that seldom change but cannot exist in the
source code.
"""

import os
from google.appengine.ext import db

class Parameter(db.Model):
    """A parameter is a constant value that is set by default."""
    value = db.BlobProperty()

def lookup(key, default):
    """Look up the given key, or return the default."""
    return Parameter.get_or_insert(key_name=key, value=default).value

SHARED_SECRET = lookup("shared_secret", os.urandom(32))

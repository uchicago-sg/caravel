from google.appengine.ext import ndb
import os

class Listing(ndb.Model):
    posted_by = ndb.StringProperty() # an email address
    title = ndb.StringProperty()
    details = ndb.TextProperty()
    posted_at = ndb.DateTimeProperty() # set to None iff not yet published

class SharedSecret(ndb.Model):
    value = ndb.BlobProperty()

SECRET_KEY = SharedSecret.get_or_insert('session_key',
                 value=os.urandom(256)).value
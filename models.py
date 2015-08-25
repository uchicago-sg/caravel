import os

from google.appengine.ext import ndb, deferred
from google.appengine.api import taskqueue

class Listing(ndb.Model):
    seller = ndb.StringProperty() # an email address
    description = ndb.StringProperty()
    details = ndb.TextProperty()
    price = ndb.IntegerProperty() # in cents of a U.S. dollar
    posted_at = ndb.DateTimeProperty() # set to None iff not yet published

class SharedSecret(ndb.Model):
    value = ndb.BlobProperty()

SECRET_KEY = SharedSecret.get_or_insert('session_key',
                 value=os.urandom(256)).value

def run_later(task, *vargs, **kwargs):
    """
    Runs the given deferrable function asynchronously.
    """

    kwargs["_retry_options"] = taskqueue.TaskRetryOptions(task_retry_limit=5)
    deferred.defer(task, *vargs, **kwargs)
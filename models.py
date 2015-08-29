import os

from google.appengine.ext import db, deferred
from google.appengine.api import taskqueue

class Listing(db.Model):
    seller = db.StringProperty() # an email address
    description = db.StringProperty()
    details = db.TextProperty()
    price = db.IntegerProperty() # in cents of a U.S. dollar
    posting_time = db.FloatProperty() # set to 0 iff not yet published

class SharedSecret(db.Model):
    value = db.BlobProperty()

SECRET_KEY = SharedSecret.get_or_insert(key_name='session_key',
                 value=os.urandom(256)).value

def run_later(task, *vargs, **kwargs):
    """
    Runs the given deferrable function asynchronously.
    """

    kwargs["_retry_options"] = taskqueue.TaskRetryOptions(task_retry_limit=5)
    deferred.defer(task, *vargs, **kwargs)
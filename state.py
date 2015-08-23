import os
import urllib2
import json
import re
import datetime

from google.appengine.ext import ndb
from google.appengine.api import deferred, taskqueue

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

    deferred.defer(task, *vargs, **kwards,
        _retry_options=taskqueue.TaskRetryOptions(task_retry_limit=5))
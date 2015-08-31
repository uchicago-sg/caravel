import os, StringIO
import photos

from google.appengine.ext import db, deferred
from google.appengine.api import taskqueue

class Listing(db.Model):
    seller = db.StringProperty() # an email address
    description = db.StringProperty()
    details = db.TextProperty()
    price = db.IntegerProperty() # in cents of a U.S. dollar
    posting_time = db.FloatProperty() # set to 0 iff not yet published

    photos_ = db.StringListProperty(indexed=False, name="photos")
    thumbnail_url = db.StringProperty(indexed=False)

    @property
    def photo_urls(self):
        """
        Gets the photo URLs for this listing.
        """

        return self.photos_

    @photo_urls.setter
    def photo_urls(self, url_or_fps):
        """
        Sets the URLs of the photos for this Listing.
        """

        # Upload a thumbnail, if one is given.
        if url_or_fps and hasattr(url_or_fps[0], 'read'):
            # Buffer first file before uploading.
            url_or_fps[0] = StringIO.StringIO(url_or_fps[0].read())
            self.thumbnail_url = photos.upload(url_or_fps[0], 'small')
            url_or_fps[0].seek(0)

        # Actually set the property on the backend.
        self.photos_ = [(photos.upload(u, 'large') if hasattr(u, 'read') else u)
                           for u in url_or_fps]

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
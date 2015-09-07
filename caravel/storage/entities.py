"""
This module defines the mapping between Datastore and Python objects.
"""
import StringIO
from caravel.storage import photos
from google.appengine.ext import db
import re

class DerivedProperty(db.Property):
    """
    A DerivedProperty allows one to create a property that is computed on
    demand when saving a property.
    """

    def __init__(self, derive_func, *args, **kwargs):
        """Initialize this property given a derivation function."""
        super(DerivedProperty, self).__init__(*args, **kwargs)
        self.derive_func = derive_func

    def __get__(self, model_instance, model_class):
        """Override when this property is read from an entity."""
        if model_instance is None:
            return self
        return self.derive_func(model_instance)

    def __set__(self, model_instance, value):
        """Block assignment to entity.prop."""
        raise db.DerivedPropertyError("cannot assign to a DerivedProperty")

class Listing(db.Expando):
    seller = db.StringProperty() # an email address
    title = db.StringProperty()
    body = db.TextProperty()
    price = db.IntegerProperty() # in cents of a U.S. dollar
    posting_time = db.FloatProperty() # set to 0 iff not yet published

    photos_ = db.StringListProperty(indexed=False, name="photos")
    thumbnail_url = db.StringProperty(indexed=False)

    @DerivedProperty
    def keywords(self):
        """Generates keywords based on the alphanumeric words in the string."""

        # Tokenize title and body (ranking them equally)
        words = self.title.split() + self.body.split()
        alphanums = [re.sub(r'[^a-z0-9]', '', word.lower()) for word in words]

        # Return a uniqified list of words.
        return sorted(set(alphanums[:500]))

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

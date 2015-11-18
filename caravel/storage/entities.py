"""
This module defines the mapping between Datastore and Python objects.
"""
import StringIO
from caravel.storage import photos
import caravel
from google.appengine.ext import db
import re
import inflect
import hashlib
INFLECT_ENGINE = inflect.engine()

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

        try:
            result = getattr(model_instance, self._attr_name())
            if result is not None:
                return result
        except AttributeError:
            pass

        return self.derive_func(model_instance)

class Versioned(db.Expando):
    version = db.IntegerProperty(default=1)
    migrations = {}

    def __init__(self, *vargs, **kwargs):
        """
        Ensure that version is set to SCHEMA_VERSION.
        """

        if 'version' not in kwargs:
            kwargs['version'] = self.__class__.SCHEMA_VERSION
        super(Versioned, self).__init__(*vargs, **kwargs)

    @classmethod
    def migration(kls, to_version):
        """
        Migrate to SCHEMA_VERSION.
        """

        def inner(func):
            kls.migrations = dict(kls.migrations)
            kls.migrations[to_version] = func
            return func
        return inner

    def migrate(self):
        while self.version < self.SCHEMA_VERSION:
            self.version += 1
            self.migrations.get(self.version, lambda _: None)(self)

    def __repr__(self):
        return "<{} key={!r}>".format(self.__class__.__name__, self.key())


def fold_query_term(word):
    """
    Returns the canonical representation of the given query word.
    """

    # block out None values.
    if word is None:
        return ""

    # if email or keyword do nothing:
    if "@" in word or ":" in word:
        return word

    # Else, singularize
    stripped = re.sub(r'[^a-z0-9]', '', word.lower())
    singularized = INFLECT_ENGINE.singular_noun(stripped) or stripped
    return singularized

class Listing(Versioned):
    SCHEMA_VERSION = 9
    CATEGORIES = [
        ("apartments", "Apartments"),
        ("subleases", "Subleases"),
        ("appliances", "Appliances"),
        ("bikes", "Bikes"),
        ("books", "Books"),
        ("cars", "Cars"),
        ("electronics", "Electronics"),
        ("employment", "Employment"),
        ("furniture", "Furniture"),
        ("miscellaneous", "Miscellaneous"),
        ("services", "Services"),
        ("wanted", "Wanted"),
        ("price:free", "Free")
    ]
    CATEGORIES_DICT = dict(CATEGORIES)

    seller = db.StringProperty() # an email address
    title = db.StringProperty(default="")
    body = db.TextProperty(default="")
    price = db.IntegerProperty(default=0) # in cents of a U.S. dollar
    posting_time = db.FloatProperty(default=0.0) # 0 iff not yet published
    categories = db.StringListProperty() # stored as keys of CATEGORIES
    admin_key = db.StringProperty(default="") # how to administer this listing
    buyers = db.StringListProperty() # how many people are interested

    photos_ = db.StringListProperty(indexed=False, name="photos")
    thumbnails_ = db.StringListProperty(indexed=False, name="thumbnails")

    @property
    def permalink(self):
        return self.key().name()

    @property
    def primary_category(self):
        return (self.categories[:1] + ["miscellaneous"])[0]

    @DerivedProperty
    def keywords(self):
        """Generates keywords based on the alphanumeric words in the string."""

        # Tokenize title and body (ranking them equally)
        words = [self.seller] + self.title.split() + self.body.split()
        words += self.categories
        if self.price == 0:
            words += ["price:free"]
        singularized = [fold_query_term(word) for word in words]

        # Return a uniqified list of words.
        return sorted(set(singularized[:500]) - set(['']))

    @property
    def photos(self):
        """
        Gets the photo URLs for this listing.
        """

        return self.photos_

    @photos.setter
    def photos(self, new_photos):
        """
        Sets the URLs of the photos for this Listing.
        """

        photo_list = []
        thumbnails = []
        for photo in new_photos:
            if not photo:
                continue
            if hasattr(photo, 'read'):
                photo = photos.upload(photo.read(), 'small', 'large')
            photo_list.append(photo)
            thumbnails.append(photo + "-small") # for old releases
        self.photos_ = photo_list
        self.thumbnails_ = thumbnails

    def put(self, *vargs, **kwargs):
        """Called when this listing is saved to the datastore."""

        # Recompute .keywords on save.
        descriptor = self.__class__.__dict__["keywords"]
        self.keywords = descriptor.derive_func(self)
        
        super(Listing, self).put(*vargs, **kwargs)

@Listing.migration(to_version=1)
def from_single_thumbnail_to_many(listing):
    if hasattr(listing, "thumbnail_url") and listing.thumbnail_url:
        listing.thumbnails_ = [listing.thumbnail_url]

@Listing.migration(to_version=6)
def recompute_keywords(listing):
    descriptor = Listing.__dict__["keywords"]
    listing.keywords = descriptor.derive_func(listing)
        # force recomputation

@Listing.migration(to_version=8)
def recompute_admin_keys(listing):
    if not listing.admin_key:
        listing.admin_key = hashlib.sha1(caravel.app.secret_key +
            ":" + listing.key().name()).hexdigest()
